import random
import requests
from bs4 import BeautifulSoup
class URPClient:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.session = requests.session()
    def login(self):
        import ddddocr
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Referer": "http://192.168.16.207:9001/loginAction.do",
            "Origin": "http://192.168.16.207:9001",
            "Content-Type": "application/x-www-form-urlencoded",
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
                print("学号或者密码不正确，请您重新输入！")
                return False
            if "你输入的验证码错误，请您重新输入！" in result:
                print("验证码识别错误，正在重新获取验证码。")
                continue
            print("登录失败，正在重新获取验证码。")
    def reset_session(self):
        self.session.close()
        self.session = requests.session()
    def get_and_evaluate_courses(self):
        evaluation_list_url = f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}"
        headers = {
            "Host": "192.168.16.207:9001",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "235",
            "Origin": "http://192.168.16.207:9001",
            "Connection": "keep-alive",
            "Referer": f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}",
            "Upgrade-Insecure-Requests": "1",
            "Priority": "u=4",
        }
        params = {
            "oper": "listWj",
            "yzxh": self.account,
        }
        response_html = self.session.get(evaluation_list_url, params=params, headers=headers).text
        soup = BeautifulSoup(response_html, "html.parser")
        unevaluated_courses = []
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
                            }
                        )
                        self.submit_evaluation(questionnaire_id, evaluatee_id, evaluation_content)
        if not unevaluated_courses:
            print("没有未评估的课程。")
    def submit_evaluation(self, questionnaire_id, evaluatee_id, evaluation_content):
        url = "http://192.168.16.207:9001/jxpgXsAction.do"
        headers1 = {
            "Host": "192.168.16.207:9001",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "235",
            "Origin": "http://192.168.16.207:9001",
            "Connection": "keep-alive",
            "Referer": f"http://192.168.16.207:9001/jxpgXsAction.do?oper=listWj&yzxh={self.account}",
            "Upgrade-Insecure-Requests": "1",
            "Priority": "u=4",
        }
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
        headers2 = {
            "Host": "192.168.16.207:9001",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://192.168.16.207:9001",
            "Connection": "keep-alive",
            "Referer": "http://192.168.16.207:9001/jxpgXsAction.do",
            "Upgrade-Insecure-Requests": "1",
            "Priority": "u=4",
        }
        result = self.session.post(submit_url, data=evaluation_data, headers=headers2).text
        if "评估成功" in result:
            print("评估成功")
        else:
            print("评估失败")
if __name__ == "__main__":
    while True:
        account = input("请输入学号: ").strip()
        password = input("请输入密码: ").strip()
        client = URPClient(account, password)
        if client.login():
            client.get_and_evaluate_courses()
        client.reset_session()
