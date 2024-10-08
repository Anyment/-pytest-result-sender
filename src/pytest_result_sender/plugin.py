from datetime import datetime

import pytest
import requests

data = {"passed": 0, "failed": 0}


def pytest_addoption(parser):
    parser.addini(
        "send_when",
        help="什么时候发送测试结果,every表示每次都发送 或者 on_fail表示只有失败时才发送",
    )
    parser.addini("send_api", help="结果发往何处")


def pytest_runtest_logreport(report: pytest.TestReport):  # 测试用例执行结果
    if report.when == "call":
        # print("本次用例执行结果：", report.outcome)
        data[report.outcome] += 1


def pytest_collection_finish(session):  # 测试用例数量
    # 用例加载完成之后执行，包含全部用例
    data["total"] = len(session.items)
    # print("用例总数：", data["total"])


def pytest_configure(config: pytest.Config):  # 测试开始时间
    # 配置加载完毕之后执行，所有测试用例执行前执行
    data["start_time"] = datetime.now()
    # print(f"{datetime.now()} pytest开始执行")

    data["send_when"] = config.getini("send_when")
    data["send_api"] = config.getini("send_api")
    # print(data['send_when'], data['send_api'])


def pytest_unconfigure():  # 测试结束时间
    # 配置卸载完毕之后执行，所有测试用例执行后执行
    data["end_time"] = datetime.now()
    # print(f"{datetime.now()} pytest结束执行")

    # 测试执行时长
    data["duration"] = data["end_time"] - data["start_time"]

    # 测试用例通过率
    data["pass_ratio"] = data["passed"] / data["total"] * 100
    data["pass_ratio"] = f"{data['pass_ratio']:.2f}%"
    # print("测试通过率：", data["pass_ratio"])

    # assert timedelta(seconds=3.5) >= data['duration'] >= timedelta(seconds=2.5)
    # assert data['total'] == 3
    # assert data['passed'] == 2
    # assert data['failed'] == 1
    # assert data['pass_ratio'] == '66.67%'

    send_result()


def send_result():
    if data["send_when"] == "on_fail" and data["failed"] == 0:
        # 只有配置失败才发送时，但failed==0，不发送
        return

    if not data["send_api"]:
        # 没有配置API地址，不发送
        return

    # 测试API是否可用
    url = data["send_api"]  # 动态制定结果发送地址
    content = f"""
    pytest自动化测试结果：
    测试时间：{data['start_time']}
    用例数量：{data['total']}
    执行时长：{data['duration']}
    测试通过：<font color='green'> {data['passed']} </font>
    测试失败：<font color='red'> {data['failed']} </font>
    测试通过率：{data['pass_ratio']}
    测试报告地址：http://baidu.com
    """

    try:
        requests.post(
            url, json={"msgtype": "markdown", "markdown": {"content": content}}
        )
    except Exception:
        pass

    data["send_done"] = 1  # 发送成功
