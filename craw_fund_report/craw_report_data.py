# encoding:utf-8
# FileName: craw_report_data
# Author:   xiaoyi | 小一
# wechat:   zhiqiuxiaoyi
# 公众号：   小一的学习笔记
# email:    zhiqiuxiaoyi@qq.com
# Date:     2021/2/18 16:34
# Description: 从天天基金网爬取基金季度报告
import os

import pandas as pd
import numpy as np
import warnings

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import random
import time

from selenium.webdriver.chrome.options import Options

warnings.filterwarnings('ignore')

# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
# pd.set_option('display.max_rows', None)


def init_selenium():
    """
    初始化 selenium
    @return:
    """
    executable_path = "D:\software\install\chromedriver_win32\chromedriver.exe"
    # 设置不弹窗显示
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=executable_path)
    # 设置弹窗显示
    # browser = webdriver.Chrome(executable_path=executable_path)

    return browser


def craw_report(browser, url):
    """
    使用 selenium 自动化测试工具爬取数据
    @param browser:
    @param url:
    @return:
    """
    """获取基金报告页的页码"""
    # 拿到网页
    browser.get(url)
    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')
    # 获取页码数
    soup_pages = soup.find_all('div', class_='pagebtns')[0].find_all('label')
    print('正在爬取第 1/{0} 页数据'.format(len(soup_pages)-2))
    df_data = use_selenium(soup)
    for index in range(1, len(soup_pages)-2):
        print('正在爬取第 {0}/{1} 页数据'.format(index+1, len(soup_pages)-2))
        # 点击下一页按钮
        browser.find_element_by_xpath("//div[@class='pagebtns']/label["+str(index+2)+"]").click()
        time.sleep(random.randint(5, 10))
        # 获取数据
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        # 解析数据并合并
        df_page_data = use_selenium(soup)
        df_data = df_data.append(df_page_data, ignore_index=True)

    return df_data


def use_selenium(soup):
    """
    爬取基金当期页的季度报告
    @param soup:
    @return:
    """
    list_result = []
    """获取内容"""
    soup_tbody = soup.find_all('table', class_='w782 comm jjgg')[0].find_all('tbody')[0]
    for soup_tr in soup_tbody.find_all('tr'):
        soup_a = soup_tr.find_all('td')[0].find_all('a')
        title = soup_a[0].get_text()
        if len(soup_a) == 2:
            link = soup_a[1].get('href')
        else:
            link = None

        date_str = soup_tr.find_all('td')[2].get_text()
        if title.endswith("报告"):
            list_result.append([title, link, date_str])

    df_result = pd.DataFrame(list_result, columns=['报告标题', '报告pdf链接', '公告日期'])
    return df_result


def get_file(df_data, dirpath):
    """
    下载基金的所有季度报告
    @param df_data:
    @param dirpath:
    @return:
    """
    for row_index, data_row in df_data.iterrows():
        report_title = data_row['报告标题']
        report_link = data_row['报告pdf链接']

        if report_link is not None:
            print('正在下载第 {0}/{1} 个报告...'.format(row_index + 1, len(df_data)))
            download_file(report_title, report_link, dirpath)
        else:
            print('正在下载第 {0}/{1} 个报告，url链接为空，请注意！！！'.format(row_index + 1, len(df_data)))
        time.sleep(random.randint(3, 5))

    print('已完成 {0} 个报告的下载，文件存储在：{1}'.format(len(df_data), dirpath))


def download_file(title, link, dirpath):
    """
    下载基金pdf报告
    @param title:
    @param link:
    @param dirpath:
    @return:
    """
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    file_path = os.path.join(dirpath, title + '.pdf')
    res = requests.get(link)
    with open(file_path, 'wb') as f:
        f.write(res.content)


if __name__ == '__main__':
    # 构造每个基金季度报告的 url
    code = '008284'
    url = 'http://fundf10.eastmoney.com/jjgg_{0}_3.html'.format(code)
    save_path_dir = os.path.join('download_file', code)

    df_data = craw_report(init_selenium(), url)
    get_file(df_data, save_path_dir)