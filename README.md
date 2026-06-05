# URP 教学评估自动化工具

一个用于自动完成 URP 教务系统教学评估的 Python 工具。

## 项目说明

本项目从独立的网站项目中分离出来进行开源，有能力的开发者可以自行在本地部署运行。
作者的网站www.meizhenxin.cn  可以查成绩学分绩点，课程表，也可以做教评等等等等，欢迎使用

## 功能特性

- 🔐 自动登录 URP 教务系统
- 🤖 自动识别验证码（基于 ddddocr）
- 📝 自动获取未评估课程列表
- ⚡ 批量完成教学评估
- 🔄 支持 Session 保持

## 环境要求

- Python 3.7+
- 可访问的 URP 教务系统

## 安装步骤

1. 克隆项目到本地

```bash
git clone https://github.com/dygzn/urp_pg.git
cd urp_jxpg
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法
main.py为经过优化但没有测试的版本，教学评估.py是没有优化但是肯定可用的完整版本
1. 打开 `main.py` 文件

2. 在文件末尾填入你的学号和密码：

```python
if __name__ == '__main__':
    # 下方填学号
    account = '你的学号'
    # 下方填密码
    password = '你的密码'

    client = URPClient(account, password)
    if client.login():
        client.get_and_evaluate_courses()
```

3. 运行程序

```bash
python main.py
```

## 配置说明

### 修改目标服务器

如果你的 URP 系统地址不是 `http://192.168.16.207:9001`，需要在代码中修改相应的 URL：

- 登录地址：[main.py:19-20, 39](main.py#L19)
- 评估列表地址：[main.py:53](main.py#L53)
- 评估提交地址：[main.py:102, 124](main.py#L102)

### 自定义评估选项

评估选项在 `submit_evaluation` 方法的 `evaluation_data` 字典中（[main.py:138-161](main.py#L138)），可根据实际需求修改评分。

## 依赖说明

- **requests**: HTTP 请求库
- **beautifulsoup4**: HTML 解析库
- **ddddocr**: 验证码识别库

## 常见问题

### Q1: 运行时提示 `TypeError: DdddOcr.__init__() got an unexpected keyword argument 'show_ad'`

**原因**：ddddocr 版本过低，不支持 `show_ad` 参数。

**解决方法**：
```bash
pip install --upgrade ddddocr>=1.5.6
```

### Q2: ddddocr 1.6.x 版本出现导入错误

**原因**：ddddocr 1.6.x 版本可能存在依赖问题。

**解决方法**：
- 方案 1：降级到稳定版本
  ```bash
  pip install ddddocr==1.5.6
  ```
- 方案 2：升级到最新版本
  ```bash
  pip install --upgrade ddddocr
  ```

### Q3: 验证码识别失败导致登录失败

**原因**：OCR 识别准确率不是 100%。

**解决方法**：重新运行程序即可，程序会自动获取新的验证码。

### Q4: 评估提交失败

**可能原因**：
- 网络连接问题
- Session 过期
- 服务器地址配置错误

**解决方法**：
1. 检查网络连接，需要在学校内网
2. 重新运行程序重新登录
3. 确认代码中的服务器地址是否正确

## 注意事项

⚠️ **重要提示**：

1. 本工具仅供学习交流使用，请勿用于非法用途
2. 使用前请确保你有权限访问目标 URP 系统
3. 请妥善保管你的账号密码，不要将包含敏感信息的代码上传到公共仓库
4. 验证码识别可能存在失败情况，如遇登录失败请重新运行
5. 评估选项为预设值，建议根据实际情况调整

## 代码结构

### 主要类和方法

- **URPClient**: URP 系统客户端类
  - `login()`: 登录方法，自动识别验证码并完成登录
  - `get_and_evaluate_courses()`: 获取未评估课程列表并自动评估
  - `submit_evaluation()`: 提交单个课程的评估

### 工作原理

1. 使用 `requests.session()` 维持会话状态
2. 通过 `ddddocr` 识别登录验证码
3. 使用 `BeautifulSoup` 解析课程列表页面
4. 自动提交评估表单完成评教

### 命名规范

本项目遵循 Python PEP 8 命名规范：
- 类名使用大驼峰命名法（如 `URPClient`）
- 方法名使用小写字母和下划线（如 `get_and_evaluate_courses`）
- 变量名使用描述性英文命名（如 `captcha_code`, `evaluation_data`）

## 本地部署

本项目已从原网站项目中独立分离，可完全在本地运行：

1. 确保 Python 环境已安装
2. 安装所需依赖包
3. 修改代码中的服务器地址为你的 URP 系统地址
4. 配置账号密码后直接运行

## 许可证

本项目仅供学习参考使用。

## 免责声明

使用本工具产生的一切后果由使用者自行承担，开发者不承担任何责任。请合理使用，遵守学校相关规定。
