AIMS Ubuntu UAT 使用说明
==========================

系统要求
- Ubuntu 22.04 LTS 或更新版本
- Python 3.11+（推荐 conda 环境 py3127）
- Git（如果通过仓库部署）

启动系统
1. 进入项目目录： cd /home/ubuntu/projects/aims
2. 激活 conda 环境： conda activate py3127
3. 执行启动脚本： bash start.sh
4. 如果配置了 Nginx 反向代理，访问 https://你的域名/
   如果没有，AIMS 仅监听 127.0.0.1:18765（本机），需要 SSH 隧道或 Nginx 才能从外部访问。

停止系统
1. 进入项目目录： cd /home/ubuntu/projects/aims
2. 执行停止脚本： bash stop.sh

日志查看

如果使用 systemd 启动（推荐）：
- sudo journalctl -u aims -f          # 实时日志（自动轮替，不会占满磁盘）
- sudo journalctl -u aims --since today  # 今天的所有日志

如果使用脚本启动（./start.sh）：
- 运行日志： logs/aims.log（自动轮替：每 10MB 切割，保留 5 个备份）
- 标准输出： logs/aims.stdout.log（需配合 logrotate 轮替）
- 错误日志： logs/aims.stderr.log（需配合 logrotate 轮替）
- 实时查看： tail -f logs/aims.log

常见问题
1. 如果端口 18765 被占用，请修改端口后重启：
   bash start.sh 18766
2. 如果启动失败，请检查 logs 目录下的错误日志。
3. 如果数据采集失败，请检查：
   - 网络连通性（从新加坡访问国内 API 可能有延迟）
   - .env 文件配置是否正确
   - 日志中的 source_errors 字段
4. 如果无法从浏览器访问，确认是否配置了 Nginx 反向代理：
   - AIMS 默认绑定 127.0.0.1（仅本机），外部无法直连
   - 必须通过 Nginx + HTTPS 或 SSH 隧道才能访问

反馈问题时请提供
1. 问题描述
2. 操作步骤
3. 实际结果
4. 期望结果
5. 截图或录屏
6. logs 目录
