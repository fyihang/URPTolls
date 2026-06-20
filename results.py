import random
import re
from urllib.parse import urldefrag

import requests
from bs4 import BeautifulSoup


class URPClient:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.session = requests.session()

    def base_headers(self):
        return {
            "Host": "192.168.16.207:9001",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def list_headers(self, referer):
        return {
            **self.base_headers(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://192.168.16.207:9001",
            "Referer": referer,
            "Priority": "u=4",
        }

    def login(self):
        import ddddocr

        # 使用验证码识别循环登录，直到成功或账号密码错误
        header = self.list_headers("http://192.168.16.207:9001/loginAction.do")
        ocr = ddddocr.DdddOcr(show_ad=False)

        while True:
            random_param = random.random()
            captcha_url = f"http://192.168.16.207:9001/validateCodeAction.do?random={random_param}"
            captcha_resp = self.session.get(captcha_url, headers=self.base_headers())
            captcha_code = ocr.classification(captcha_resp.content)
            data = {
                "zjh1": "",
                "tips": "",
                "lx": "",
                "evalue": "",
                "eflag": "",
                "fs": "",
                "dzslh": "",
                "zjh": self.account,
                "mm": self.password,
                "v_yzm": captcha_code,
            }
            result = self.session.post(
                "http://192.168.16.207:9001/loginAction.do",
                data=data,
                headers=header,
            ).text
            if "学分制综合教务" in result:
                return True
            if "您的密码不正确，请您重新输入！" in result:
                print("学号或者密码不正确，请重新输入")
                return False
            if "你输入的验证码错误，请您重新输入！" in result:
                print("验证码识别错误，正在重新获取验证码")
                continue
            print("登录失败，正在重新获取验证码")

    def get_student_name(self):
        # 读取姓名
        page_sources = [
            "http://192.168.16.207:9001/menu/top.jsp",
            f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}",
            "http://192.168.16.207:9001/framework/main.jsp",
        ]
        for url in page_sources:
            response_html = self.session.get(url, headers={**self.base_headers(), "Referer": url}).text
            student_name = self.parse_current_user_name(response_html)
            if student_name:
                return student_name
        return None

    def parse_current_user_name(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for td in soup.find_all("td", nowrap=True):
            cell_text = td.get_text(" ", strip=True).replace("\xa0", " ")
            if "当前用户" not in cell_text or self.account not in cell_text:
                continue
            match = re.search(rf"{re.escape(self.account)}[\(（]([^()（）]+)[\)）]", cell_text)
            if match:
                return match.group(1).strip()
            match = re.search(r"当前用户[:：]?\s*[^()（）]*[\(（]([^()（）]+)[\)）]", cell_text)
            if match:
                return match.group(1).strip()
        return None

    def fetch_grade_page(self):
        # 先获取每学期成绩首页，再从中跳转到“全部学期查询”
        url = "http://192.168.16.207:9001/gradeLnAllAction.do?type=ln&oper=qbcj"
        response = self.session.get(url, headers=self.list_headers(url))
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def fetch_all_semester_page(self, html):
        # 定位“全部学期查询”入口，进入包含所有学期成绩的页面
        soup = BeautifulSoup(html, "html.parser")
        base_url = "http://192.168.16.207:9001/gradeLnAllAction.do?type=ln&oper=qbcj"
        for a in soup.find_all("a", href=True):
            text = self._normalize_text(a.get_text(" ", strip=True))
            href = a["href"]
            if "全部学期查询" in text or "oper=qbcj" in href:
                clean_href, _ = urldefrag(href)
                next_url = requests.compat.urljoin("http://192.168.16.207:9001/", clean_href)
                response = self.session.get(next_url, headers=self.list_headers(base_url))
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
        return html

    def fetch_gpa_page(self):
        url = "http://192.168.16.207:9001/gradeLnAllAction.do?oper=queryXfjd"
        response = self.session.get(url, headers=self.list_headers(url))
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    @staticmethod
    def _normalize_text(text):
        return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

    def parse_latest_semester_courses(self, html):
        # 按学期表格顺序取最后一张成绩表，视为最新学期
        soup = BeautifulSoup(html, "html.parser")
        semester_pattern = re.compile(r".*学年.*学期.*|.*学期.*")
        semester_titles = []
        grade_tables = []

        for td in soup.find_all("td"):
            text = self._normalize_text(td.get_text(" ", strip=True))
            if semester_pattern.search(text):
                if text not in semester_titles:
                    semester_titles.append(text)

        for table in soup.find_all("table", id="user"):
            grade_tables.append(table)

        if not grade_tables:
            return (semester_titles[-1] if semester_titles else None), []

        def parse_table(grade_table):
            courses = []
            for tr in grade_table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 8:
                    continue
                row_text = self._normalize_text(tr.get_text(" ", strip=True))
                if any(name in row_text for name in ("课程号", "课序号", "课程名", "英文课程名", "学分", "课程属性", "是否学位课", "成绩")):
                    continue

                course_name = self._normalize_text(tds[2].get_text(" ", strip=True))
                course_attr = self._normalize_text(tds[5].get_text(" ", strip=True))
                grade_cell = tds[-1]
                grade_text = self._normalize_text(grade_cell.get_text(" ", strip=True))
                if not grade_text:
                    p_tag = grade_cell.find("p")
                    if p_tag:
                        grade_text = self._normalize_text(p_tag.get_text(" ", strip=True))

                if not course_name or course_name in {"合计", "平均分", "总计"}:
                    continue
                if not grade_text or grade_text in {"-", "--"}:
                    continue

                courses.append((course_name, course_attr, grade_text))
            return courses

        latest_semester = semester_titles[-1] if semester_titles else "最新学期"
        latest_grade_table = grade_tables[-1]
        courses = parse_table(latest_grade_table)
        if courses:
            return latest_semester, courses

        for grade_table in reversed(grade_tables[:-1]):
            courses = parse_table(grade_table)
            if courses:
                return latest_semester, courses

        return latest_semester, []

    def parse_gpa_info(self, html):
        # 绩点页的表格固定为三条数据，按行顺序读取三项绩点
        soup = BeautifulSoup(html, "html.parser")
        gpa_table = soup.find("table", id="user")
        if not gpa_table:
            return None

        rows = gpa_table.find_all("tr")
        values = []
        for tr in rows[1:4]:
            input_tag = tr.find("input")
            if input_tag and input_tag.get("value") is not None:
                values.append(self._normalize_text(str(input_tag.get("value", ""))))
            else:
                match = re.search(r'value\s*=\s*"([^"]+)"', str(tr))
                values.append(self._normalize_text(match.group(1)) if match else "")

        if len(values) < 3:
            return None

        return {
            "学分绩点": values[0],
            "学位绩点": values[1],
            "加权学分学位绩点": values[2],
        }

    def print_latest_semester_results(self):
        # 先打印姓名，再打印成绩，最后打印绩点
        student_name = self.get_student_name()
        if student_name:
            print(f"{student_name}登录成功")
        else:
            print("登录成功")

        html = self.fetch_grade_page()
        html = self.fetch_all_semester_page(html)
        semester, courses = self.parse_latest_semester_courses(html)

        if not semester:
            print("未找到成绩数据")
            return False
        if not courses:
            print(f"已找到最新学期：{semester}，但未解析到课程成绩")
            return False

        for course_name, course_attr, grade in courses:
            print(f"{course_name}:{course_attr}:{grade}")

        gpa_html = self.fetch_gpa_page()
        gpa_info = self.parse_gpa_info(gpa_html)
        if gpa_info:
            print(
                f"学分绩点:{gpa_info.get('学分绩点', '')}|"
                f"学位绩点:{gpa_info.get('学位绩点', '')}|"
                f"加权学分学位绩点:{gpa_info.get('加权学分学位绩点', '')}"
            )
        return True


if __name__ == "__main__":
    # 支持连续查询多个账号，每轮结束后重置会话回到登录
    while True:
        account = input("请输入学号: ").strip()
        password = input("请输入密码: ").strip()
        client = URPClient(account, password)
        if client.login():
            client.print_latest_semester_results()
        client.session.close()
