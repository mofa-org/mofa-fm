"""
Website to Podcast ingestion service.
独立于 RSS 的网页转播客功能。
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class WebContent:
    """网页内容提取结果"""
    url: str
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    word_count: int = 0


def _validate_url(url: str) -> str:
    """验证 URL 格式"""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url


def _clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    # 解码 HTML 实体
    text = html.unescape(text)
    # 合并多个空白字符
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    return text.strip()


def _extract_with_readability(html_content: str, url: str) -> WebContent:
    """
    使用 readability-lxml 算法提取正文
    如果没有安装 readability，使用 BeautifulSoup 回退
    """
    try:
        from readability import Document
        # 清理 HTML 中的非法字符
        cleaned_html = _clean_html_for_xml(html_content)
        doc = Document(cleaned_html)
        title = doc.short_title() or doc.title()
        summary = doc.summary()
        # 从 summary HTML 中提取纯文本
        soup = BeautifulSoup(summary, 'html.parser')
        content = _clean_text(soup.get_text(separator='\n\n'))
        return WebContent(
            url=url,
            title=_clean_text(title),
            content=content,
            word_count=len(content)
        )
    except Exception as e:
        # 任何错误都回退到 BeautifulSoup
        print(f"Readability failed: {e}, falling back to BeautifulSoup")
        return _extract_with_beautifulsoup(html_content, url)


def _clean_html_for_xml(html_content: str) -> str:
    """清理 HTML 中的非法 XML 字符"""
    # 移除 NULL 字节和控制字符
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', html_content)
    return cleaned


def _extract_with_beautifulsoup(html_content: str, url: str) -> WebContent:
    """
    使用 BeautifulSoup 提取正文
    启发式算法：找最长文本段落所在的容器
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除脚本、样式、导航等无关元素
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
        tag.decompose()

    # 提取标题
    title = ""
    if soup.title:
        title = _clean_text(soup.title.string)
    if not title and soup.find('h1'):
        title = _clean_text(soup.find('h1').get_text())

    # 尝试找 article 或 main 标签
    article = soup.find('article') or soup.find('main')
    if article:
        content = _clean_text(article.get_text(separator='\n\n'))
        return WebContent(
            url=url,
            title=title,
            content=content,
            word_count=len(content)
        )

    # 启发式：找文本密度最高的 div
    best_content = ""
    best_score = 0

    for tag in soup.find_all(['div', 'section']):
        text = tag.get_text(separator='\n')
        text_len = len(text.strip())
        link_text = sum(len(a.get_text()) for a in tag.find_all('a'))

        # 评分：文本长度 - 链接文本（惩罚链接多的区域）
        score = text_len - link_text * 2

        if score > best_score and text_len > 200:
            best_score = score
            best_content = _clean_text(text)

    # 如果没找到，取 body 的全部文本
    if not best_content and soup.body:
        best_content = _clean_text(soup.body.get_text(separator='\n\n'))

    return WebContent(
        url=url,
        title=title,
        content=best_content,
        word_count=len(best_content)
    )


def _fetch_with_selenium(url: str, timeout: int = 30) -> WebContent:
    """
    使用 Selenium 抓取 JavaScript 动态加载的网页内容
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        # 尝试使用系统安装的 chromium-browser
        try:
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            # 如果系统 chromedriver 失败，尝试让 selenium 自动查找
            driver = webdriver.Chrome(options=chrome_options)

        driver.get(url)

        # 等待页面加载完成
        wait = WebDriverWait(driver, timeout)

        # 等待 body 标签出现
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 额外等待 JavaScript 渲染（给动态内容加载时间）
        time.sleep(5)

        # 获取页面标题
        title = driver.title or ""

        # 直接获取 body 文本（这样可以拿到动态加载的所有内容）
        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text

        # 清理文本
        cleaned_text = _clean_text(text)

        return WebContent(
            url=url,
            title=_clean_text(title),
            content=cleaned_text,
            word_count=len(cleaned_text)
        )

    finally:
        if driver:
            driver.quit()


def fetch_webpage_content(url: str, timeout: int = 30, use_selenium: bool = False) -> WebContent:
    """
    抓取网页并提取内容

    Args:
        url: 网页 URL
        timeout: 请求超时时间（秒）
        use_selenium: 是否使用 Selenium 抓取（用于 JavaScript 动态加载的页面）

    Returns:
        WebContent: 提取的网页内容
    """
    url = _validate_url(url)

    # 如果使用 Selenium 或普通请求获取的内容太少，使用 Selenium
    if use_selenium:
        return _fetch_with_selenium(url, timeout)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    # 检测编码 - 使用 apparent_encoding 作为首选
    if response.encoding:
        response.encoding = response.apparent_encoding

    html_content = response.text

    # 优先使用 readability，回退到 BeautifulSoup
    result = _extract_with_readability(html_content, url)

    # 如果内容太少，尝试使用 Selenium
    # 阈值设为3000字符，因为有些网站虽然能抓到1000+字符，但只是通用介绍而非文章主体
    if len(result.content) < 3000:
        print(f"Content too short ({len(result.content)} chars), trying Selenium...")
        try:
            return _fetch_with_selenium(url, timeout)
        except Exception as e:
            print(f"Selenium failed: {e}, returning original result")

    return result


def generate_podcast_script_from_web(
    content: WebContent,
    style: str = "news_flash",
    speakers: Optional[list] = None
) -> str:
    """
    将网页内容转换为播客脚本

    Args:
        content: 网页内容
        style: 播客风格 (news_flash, interview, storytelling)
        speakers: 说话人配置

    Returns:
        str: 生成的播客脚本
    """
    from django.conf import settings
    from openai import OpenAI

    # 初始化 OpenAI 客户端
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise ValueError('OPENAI_API_KEY 未配置')

    client = OpenAI(
        api_key=api_key,
        base_url=getattr(settings, 'OPENAI_API_BASE', 'https://api.moonshot.cn/v1'),
        timeout=90,
    )
    model = getattr(settings, 'OPENAI_MODEL', 'moonshot-v1-8k')

    # 构建提示词
    system_prompt = """你是一位专业的播客脚本创作者。请将用户提供的网页内容改写成对话形式的播客脚本。

要求：
1. 使用对话形式，两个主持人（【大牛】、【一帆】）讨论这篇文章
2. 【大牛】是主持人，负责引导话题、提问和总结；【一帆】是嘉宾，负责分享观点、回答问题
3. 保留文章的核心观点和关键信息
4. 语言口语化，适合播客收听
5. 开头有简短的引入，结尾有总结
6. 格式：【大牛】说话内容... 【一帆】说话内容...
7. 每个段落都要有角色标记，不要有大段旁白
8. **重要：直接输出纯净的 Markdown 文本，不要用 ```markdown 代码块包裹**

特殊情况处理：
- 如果原文内容很少（少于2000字）或看起来只是网页的通用介绍而非文章主体，请基于文章标题和URL中的关键信息，结合你对该主题的专业知识，生成一个合理的播客脚本
- 例如标题提到"2026年三大开源语音合成模型TTS推荐与测评"，就应该围绕这三个具体模型展开讨论，而不是泛泛地聊TTS技术历史
"""

    content_text = content.content if len(content.content) > 500 else f"[网页内容提取不完整，请基于标题'{content.title}'和主题生成内容]"

    user_prompt = f"""原文标题：{content.title}
原文链接：{content.url}

原文内容：
{content_text}

请生成播客脚本："""

    # 调用 AI 生成脚本
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    script = response.choices[0].message.content.strip()
    return script


# 简单的测试函数
def test_fetch():
    """测试网页抓取"""
    test_url = "https://stevejobsarchive.com/stories/stay-hungry-stay-foolish"
    try:
        content = fetch_webpage_content(test_url)
        print(f"标题: {content.title}")
        print(f"字数: {content.word_count}")
        print(f"\n前 500 字:\n{content.content[:500]}...")
        return content
    except Exception as e:
        print(f"抓取失败: {e}")
        raise


if __name__ == "__main__":
    test_fetch()
