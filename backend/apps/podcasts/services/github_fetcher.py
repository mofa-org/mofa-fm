"""
GitHub 文件获取服务
用于从 GitHub 仓库获取 README 等文件内容
"""

import re
import requests
from typing import Dict, Optional
from urllib.parse import urlparse


class GitHubFetcher:
    """GitHub 文件获取器"""

    RAW_URL_TEMPLATE = "https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    TIMEOUT = 15  # 秒

    # 常见的 README 文件名（按优先级排序）
    README_FILENAMES = [
        'README.md',
        'readme.md',
        'Readme.md',
        'README.MD',
        'README.txt',
        'README',
    ]

    # 尝试的分支名称
    BRANCH_NAMES = ['main', 'master']

    @classmethod
    def parse_github_url(cls, url: str) -> Dict:
        """
        解析 GitHub URL，支持仓库 URL 和文件 URL

        支持的格式：
        - https://github.com/owner/repo
        - https://github.com/owner/repo/
        - https://github.com/owner/repo/blob/main/README.md
        - https://github.com/owner/repo/tree/main/docs

        Returns:
            {
                'success': bool,
                'owner': str,
                'repo': str,
                'ref': str or None,  # 分支名
                'path': str or None,  # 文件路径
                'error': str or None
            }
        """
        if not url or not url.strip():
            return {'success': False, 'error': 'URL不能为空'}

        url = url.strip()

        # 解析 URL
        try:
            parsed = urlparse(url)

            # 检查域名
            if parsed.netloc not in ['github.com', 'www.github.com']:
                return {'success': False, 'error': '仅支持 github.com 域名'}

            # 提取路径部分
            path_parts = [p for p in parsed.path.split('/') if p]

            if len(path_parts) < 2:
                return {'success': False, 'error': 'URL格式不正确，缺少 owner/repo'}

            owner = path_parts[0]
            repo = path_parts[1]

            # 检查是否是文件链接（包含 blob 或 tree）
            ref = None
            file_path = None

            if len(path_parts) > 2:
                if path_parts[2] in ['blob', 'tree']:
                    # 格式: /owner/repo/blob/branch/path/to/file
                    if len(path_parts) > 3:
                        ref = path_parts[3]
                        if len(path_parts) > 4:
                            file_path = '/'.join(path_parts[4:])

            return {
                'success': True,
                'owner': owner,
                'repo': repo,
                'ref': ref,
                'path': file_path
            }

        except Exception as e:
            return {'success': False, 'error': f'URL解析失败: {str(e)}'}

    @classmethod
    def fetch_readme(
        cls,
        owner: str,
        repo: str,
        ref: Optional[str] = None,
        path: Optional[str] = None
    ) -> Dict:
        """
        从 GitHub 获取 README 内容

        Args:
            owner: GitHub 用户名或组织名
            repo: 仓库名
            ref: 分支名（可选，会自动尝试 main 和 master）
            path: 文件路径（可选，会自动尝试多个 README 文件名）

        Returns:
            {
                'success': bool,
                'content': str,           # README 内容
                'size': int,              # 字节数
                'owner': str,
                'repo': str,
                'ref': str,               # 实际使用的分支
                'path': str,              # 实际使用的路径
                'raw_url': str,           # 原始文件 URL
                'error': str or None
            }
        """
        # 确定要尝试的分支列表
        branches_to_try = [ref] if ref else cls.BRANCH_NAMES

        # 确定要尝试的文件路径列表
        if path:
            paths_to_try = [path]
        else:
            paths_to_try = cls.README_FILENAMES

        # 尝试所有组合
        last_error = None

        for branch in branches_to_try:
            for file_path in paths_to_try:
                try:
                    raw_url = cls.RAW_URL_TEMPLATE.format(
                        owner=owner,
                        repo=repo,
                        ref=branch,
                        path=file_path
                    )

                    response = requests.get(
                        raw_url,
                        timeout=cls.TIMEOUT,
                        headers={'User-Agent': 'MoFA-FM-Bot'}
                    )

                    if response.status_code == 200:
                        content = response.text

                        if not content.strip():
                            last_error = '文件内容为空'
                            continue

                        return {
                            'success': True,
                            'content': content,
                            'size': len(content.encode('utf-8')),
                            'owner': owner,
                            'repo': repo,
                            'ref': branch,
                            'path': file_path,
                            'raw_url': raw_url
                        }

                    elif response.status_code == 404:
                        last_error = '文件未找到'
                        continue

                    else:
                        last_error = f'HTTP {response.status_code}'
                        continue

                except requests.exceptions.Timeout:
                    last_error = '请求超时（15秒）'
                    continue

                except requests.exceptions.RequestException as e:
                    last_error = f'网络请求失败: {str(e)}'
                    continue

                except Exception as e:
                    last_error = f'未知错误: {str(e)}'
                    continue

        # 所有尝试都失败
        return {
            'success': False,
            'error': last_error or '未找到README文件'
        }

    @classmethod
    def import_github_readme(cls, url: str) -> Dict:
        """
        一站式导入方法：解析 URL 并获取 README

        Args:
            url: GitHub 仓库 URL 或 README 文件 URL

        Returns:
            {
                'success': bool,
                'content': str,
                'size': int,
                'owner': str,
                'repo': str,
                'ref': str,
                'path': str,
                'raw_url': str,
                'github_url': str,  # 原始 GitHub URL
                'error': str or None
            }
        """
        # 1. 解析 URL
        parse_result = cls.parse_github_url(url)

        if not parse_result['success']:
            return parse_result

        # 2. 获取 README
        fetch_result = cls.fetch_readme(
            owner=parse_result['owner'],
            repo=parse_result['repo'],
            ref=parse_result.get('ref'),
            path=parse_result.get('path')
        )

        if not fetch_result['success']:
            return fetch_result

        # 3. 返回完整结果
        return {
            **fetch_result,
            'github_url': url
        }
