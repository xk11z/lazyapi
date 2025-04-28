import argparse
import requests
from bs4 import BeautifulSoup
import pyfiglet
import concurrent.futures
import time
import logging

# 配置日志，去掉时间显示
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def generate_ascii_art(text):
    """
    生成 ASCII 艺术字
    :param text: 要转换为 ASCII 艺术字的文本
    :return: ASCII 艺术字字符串
    """
    return pyfiglet.figlet_format(text)


def parse_arguments():
    """
    解析命令行参数
    :return: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(description='请求 URL 并返回状态码、网站标题和响应长度')
    parser.add_argument('-f', '--file', help='包含 URL 地址的文件路径')
    parser.add_argument('-u', '--url', help='基础 URL')
    parser.add_argument('-o', '--output', help='保存结果的 TXT 文件路径')
    parser.add_argument('-d', '--direct', action='store_true', help='直接请求 -f 参数的 URL，不进行拼接')
    parser.add_argument('-m', '--method', default='get', help='指定请求方法，支持 get、post、put、delete')
    parser.add_argument('-c', '--status-code', type=int, nargs='+',
                        help='指定要返回的状态码，可指定多个，默认返回全部状态码')
    parser.add_argument('-p', '--parameters', help='指定请求参数，多个参数用逗号分隔，如 key1=value1,key2=value2')
    parser.add_argument('-t', '--threads', type=int, default=1, help='指定线程数')
    parser.add_argument('-H', '--headers', help='指定请求 headers，多个 headers 用逗号分隔，如 key1=value1,key2=value2')
    parser.add_argument('-r', '--response-body', action='store_true', help='返回完整响应体')
    return parser.parse_args()


def parse_parameters(parameters_str):
    """
    解析请求参数
    :param parameters_str: 参数字符串，格式为 "key1=value1,key2=value2"
    :return: 解析后的参数字典
    """
    params = {}
    if parameters_str:
        param_pairs = parameters_str.split(',')
        for pair in param_pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = value
    return params


def get_url_info(url, method='get', params=None, headers=None):
    """
    获取 URL 的相关信息，包括状态码、标题、响应长度等
    :param url: 请求的 URL
    :param method: 请求方法，默认为 get
    :param params: 请求参数
    :param headers: 请求 headers
    :return: 状态码、标题、响应长度、Content-Type、Server、响应时间、重定向历史、响应体
    """
    try:
        start_time = time.time()
        if method.lower() == 'get':
            response = requests.get(url, params=params, headers=headers)
        elif method.lower() == 'post':
            response = requests.post(url, data=params, headers=headers)
        elif method.lower() == 'put':
            response = requests.put(url, data=params, headers=headers)
        elif method.lower() == 'delete':
            response = requests.delete(url, params=params, headers=headers)
        else:
            logging.error(f"不支持的请求方法: {method}")
            return None, None, None, None, None, None, None, None

        end_time = time.time()
        status_code = response.status_code
        response_length = len(response.content)

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else '未找到标题'

        content_type = response.headers.get('Content-Type', '未找到 Content-Type')
        lower_case_headers = {k.lower(): v for k, v in response.headers.items()}
        server = lower_case_headers.get('server', '未找到 Server')
        response_time = end_time - start_time

        return status_code, title, response_length, content_type, server, response_time, response.history, response.text
    except requests.RequestException as e:
        logging.error(f"请求 {url} 时出错: {e}")
        return None, None, None, None, None, None, None, None


def format_output(full_url, status_code, title, response_length, method, params, headers, content_type, server, response_time,
                  redirect_count, final_url, response_body=None):
    """
    格式化输出信息
    :param full_url: 请求的完整 URL
    :param status_code: 状态码
    :param title: 网站标题
    :param response_length: 响应长度
    :param method: 请求方法
    :param params: 请求参数
    :param headers: 请求 headers
    :param content_type: Content-Type
    :param server: Server 信息
    :param response_time: 响应时间
    :param redirect_count: 重定向次数
    :param final_url: 最终 URL
    :param response_body: 响应体
    :return: 格式化后的输出字符串
    """
    output = f"    URL: {full_url}\n"
    output += f"    状态码: {status_code}\n"
    output += f"    网站标题: {title}\n"
    output += f"    响应长度: {response_length} 字节\n"
    output += f"    请求方法: {method}\n"
    output += f"    请求参数: {params}\n"
    output += f"    请求 headers: {headers}\n"
    output += f"    Content-Type: {content_type}\n"
    output += f"    Server: {server}\n"
    output += f"    响应时间: {response_time:.2f} 秒\n"
    output += f"    重定向次数: {redirect_count}\n"
    output += f"    最终 URL: {final_url}\n"
    if response_body:
        output += f"    响应体:\n{response_body}\n"
    output += "-" * 50 + "\n"
    return output


def process_url(full_url, args, params, headers, output_lines):
    """
    处理单个 URL 的请求并输出结果
    :param full_url: 请求的完整 URL
    :param args: 命令行参数对象
    :param params: 请求参数
    :param headers: 请求 headers
    :param output_lines: 存储输出结果的列表
    """
    status_code, title, response_length, content_type, server, response_time, history, response_body = get_url_info(full_url,
                                                                                                     args.method,
                                                                                                     params,
                                                                                                     headers)
    if status_code is not None:
        if args.status_code is None or status_code in args.status_code:
            redirect_count = len(history)
            final_url = full_url if not history else history[-1].headers.get('Location', full_url)
            output = format_output(full_url, status_code, title, response_length, args.method, params, headers, content_type,
                                   server, response_time, redirect_count, final_url, response_body if args.response_body else None)
            output_lines.append(output)
            logging.info(output.strip())


def main():
    """
    主函数，程序入口
    """
    # 打印 ASCII 艺术字
    ascii_art = generate_ascii_art("lazyapi")
    print(ascii_art)
    print("made by xk11z 2025/4/28  V1.0")

    args = parse_arguments()
    output_lines = []

    if not args.file and not args.url:
        parser = argparse.ArgumentParser(description='请求 URL 并返回状态码、网站标题和响应长度')
        parser.add_argument('-f', '--file', help='包含 URL 地址的文件路径')
        parser.add_argument('-u', '--url', help='BaseURL')
        parser.add_argument('-o', '--output', help='保存结果的 TXT 文件路径')
        parser.add_argument('-d', '--direct', action='store_true', help='直接请求 -f 参数的 URL，不进行拼接')
        parser.add_argument('-m', '--method', default='get', help='指定请求方法，支持 get、post、put、delete')
        parser.add_argument('-c', '--status-code', type=int, nargs='+',
                            help='指定要返回的状态码，可指定多个，默认返回全部状态码')
        parser.add_argument('-p', '--parameters', help='指定请求参数，多个参数用逗号分隔，如 user=value1,pass=value2')
        parser.add_argument('-t', '--threads', type=int, default=1, help='指定线程数')
        parser.add_argument('-H', '--headers', help='指定请求 headers，多个 headers 用逗号分隔，如 Referer=value1,Cookie=value2')
        parser.add_argument('-r', '--response-body', action='store_true', help='返回完整响应体')
        parser.print_help()
        return

    params = parse_parameters(args.parameters)
    headers = parse_parameters(args.headers)

    if args.file and args.url:
        try:
            # 指定编码格式为 utf-8
            with open(args.file, 'r', encoding='utf-8') as file:
                urls = []
                for line in file:
                    sub_url = line.strip()
                    if args.direct:
                        full_url = sub_url
                    else:
                        full_url = args.url.rstrip('/') + '/' + sub_url.lstrip('/')
                    urls.append(full_url)

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.threads)
            futures = [executor.submit(process_url, url, args, params, headers, output_lines) for url in urls]
            try:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                logging.info("接收到中断信号，正在关闭线程池...")
                executor.shutdown(wait=False)
                return
        except FileNotFoundError:
            logging.error(f"文件 {args.file} 未找到。")
    elif args.url:
        process_url(args.url, args, params, headers, output_lines)
    else:
        logging.info("请提供有效的 -f 文件路径或 -u URL。")

    if args.output and output_lines:
        try:
            with open(args.output, 'w', encoding='utf-8') as output_file:
                for line in output_lines:
                    output_file.write(line)
            logging.info(f"结果已保存到 {args.output}")
        except Exception as e:
            logging.error(f"保存结果到文件时出错: {e}")


if __name__ == "__main__":
    main()