# lazyapi

平时喜欢用findsomething，雪瞳等插件
插件可获取api相对路径，绝对路径
于是写了个工具可批量请求，返回网站标题响应长度等信息
基础用法：
-u是基础url
-f包含 URL 地址的文件路径
-d直接请求url不加基础url
-m指定请求方法，支持 get、post、put、delete
-p指定请求参数，多个参数用逗号分隔，如 user=value1,pass=value2
-H指定请求头，多个 headers 用逗号分隔，如 Referer=value1,Cookie=value2
-o保存结果的 TXT 文件路径
-r返回完整响应体
-t指定线程数
-c指定要返回的状态码，可指定多个，默认返回全部状态码
