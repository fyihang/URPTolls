import random
import requests
from bs4 import BeautifulSoup
class URPClient:
    def __init__(self, account, password):
        # 保存当前登录账号和密码，并维持同一会话
        self.account = account
        self.password = password
        self.session = requests.session()

    def base_headers(self):
        # 公共浏览器请求头，供后续请求复用
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
        # 列表/提交类请求在公共头基础上补充表单相关字段
        return {
            **self.base_headers(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://192.168.16.207:9001",
            "Referer": referer,
            "Priority": "u=4",
        }

    def get_student_name(self):
        # 从顶部框架或相关页面中读取“当前用户”信息
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
        import re

        # 精确定位 td nowrap 单元格，解析括号中的姓名
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

    def login(self):
        import ddddocr
        # 循环识别验证码，直到登录成功或账号密码错误
        header = {
            **self.list_headers("http://192.168.16.207:9001/loginAction.do"),
        }
        ocr = ddddocr.DdddOcr(show_ad=False)
        while True:
            random_param = random.random()
            captcha_url = f"http://192.168.16.207:9001/validateCodeAction.do?random={random_param}"
            captcha_resp = self.session.get(captcha_url)
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
                print("登录成功")
                return True
            if "您的密码不正确，请您重新输入！" in result:
                print("学号或者密码不正确，请重新输入")
                return False
            if "你输入的验证码错误，请您重新输入！" in result:
                print("验证码识别错误，正在重新获取验证码")
                continue
            print("登录失败，正在重新获取验证码")
    def reset_session(self):
        # 结束后重置会话，便于下一次重新登录
        self.session.close()
        self.session = requests.session()
    def get_and_evaluate_courses(self, student_name):
        # 拉取未评课程并逐门提交，失败项交给重试逻辑
        evaluation_list_url = f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}"
        headers = self.list_headers(evaluation_list_url)
        params = {
            "oper": "listWj",
            "yzxh": self.account,
        }
        response_html = self.session.get(evaluation_list_url, params=params, headers=headers).text
        soup = BeautifulSoup(response_html, "html.parser")
        unevaluated_courses = []
        all_success = True
        failed_courses = []
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 4 and tds[3].get_text(strip=True) == "否":
                img_tag = tr.find("img")
                if img_tag and "name" in img_tag.attrs:
                    name_field = img_tag["name"]
                    parts = name_field.split("#@")
                    if len(parts) >= 6:
                        questionnaire_id = parts[0]
                        evaluatee_id = parts[1]
                        evaluation_content = parts[5]
                        teacher_name = parts[2]
                        course_name = parts[4]
                        print(f"未评课程：{course_name}，教师：{teacher_name}")
                        unevaluated_courses.append(
                            {
                                "questionnaire_id": questionnaire_id,
                                "evaluatee_id": evaluatee_id,
                                "evaluation_content": evaluation_content,
                                "course_name": course_name,
                            }
                        )
                        if not self.submit_evaluation(questionnaire_id, evaluatee_id, evaluation_content):
                            all_success = False
                            failed_courses.append(
                                {
                                    "questionnaire_id": questionnaire_id,
                                    "evaluatee_id": evaluatee_id,
                                    "evaluation_content": evaluation_content,
                                    "course_name": course_name,
                                }
                            )
        if not unevaluated_courses:
            print("没有未评估的课程")
        if not all_success:
            for course in failed_courses:
                if not self.retry_submit_course(student_name, course):
                    return False
        return True

    def retry_submit_course(self, student_name, course):
        # 单门课程最多重试三次，仍失败则记录明确提示
        for attempt in range(1, 4):
            if self.submit_evaluation(
                course["questionnaire_id"],
                course["evaluatee_id"],
                course["evaluation_content"],
            ):
                return True
        print(f"{student_name}的{course['course_name']}未成功评估")
        return False
    def submit_evaluation(self, questionnaire_id, evaluatee_id, evaluation_content):
        # 先打开评估表单页，再提交自动填写的评估内容
        url = "http://192.168.16.207:9001/jxpgXsAction.do"
        headers1 = self.list_headers(f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}")
        data = {
            "wjbm": questionnaire_id,
            "bpr": evaluatee_id,
            "pgnr": evaluation_content,
            "oper": "wjShow",
        }
        response_html = self.session.post(url, data=data, headers=headers1).text
        soup = BeautifulSoup(response_html, "html.parser")
        evaluation_data = {
            "wjbm": questionnaire_id,
            "bpr": evaluatee_id,
            "pgnr": evaluation_content,
            "xumanyzg": "zg",
            "wjbz": "",
            "zgpj": "",
        }
        for tr in soup.find_all("tr"):
            input_tags = tr.find_all("input")
            question_ids = []
            options = []
            for inp in input_tags:
                name = inp.get("name", "")
                inp_type = inp.get("type", "text")
                value = inp.get("value", "")
                if name.isdigit():
                    if name not in question_ids:
                        question_ids.append(name)
                    if inp_type in {"radio", "checkbox"}:
                        options.append((name, value))
            if question_ids:
                for qid in question_ids:
                    if qid not in evaluation_data:
                        q_options = [(n, v) for n, v in options if n == qid]
                        if q_options:
                            best = max(
                                q_options,
                                key=lambda x: float(x[1].split("_")[0]) if "_" in x[1] else 0,
                            )
                            evaluation_data[qid] = best[1]
        for inp in soup.find_all(["input", "textarea"]):
            name = inp.get("name", "")
            if name.isdigit() and name not in evaluation_data:
                inp_type = inp.get("type", "text")
                if inp_type == "radio" and inp.get("checked"):
                    evaluation_data[name] = inp.get("value", "")
                else:
                    evaluation_data[name] = ""
        submit_url = "http://192.168.16.207:9001/jxpgXsAction.do?oper=wjpg"
        headers2 = self.list_headers("http://192.168.16.207:9001/jxpgXsAction.do")
        result = self.session.post(submit_url, data=evaluation_data, headers=headers2).text
        if "评估成功" in result:
            print("评估成功")
            return True
        else:
            print("评估失败")
            return False
if __name__ == "__main__":
    # 支持连续登录多个账号，每轮结束后重置会话
    while True:
        account = input("请输入学号: ").strip()
        password = input("请输入密码: ").strip()
        client = URPClient(account, password)
        if client.login():
            student_name = client.get_student_name()
            if client.get_and_evaluate_courses(student_name):
                if student_name:
                    print(f"{student_name}的教学评估已完成")
                else:
                    print("教学评估已完成")
        client.reset_session()
