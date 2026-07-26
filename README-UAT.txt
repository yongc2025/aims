AIMS Ubuntu UAT 使用说明
==========================

系统要求
- Ubuntu 22.04 LTS 或更新版本
- Python 3.11+
- Git（如果通过仓库部署）

启动系统
1. 进入项目目录： cd /opt/aims
2. 执行启动脚本： bash start.sh
3. 访问 http://<服务器IP>:8000/

停止系统
1. 进入项目目录： cd /opt/aims
2. 执行停止脚本： bash stop.sh

日志查看
- 运行日志： logs/aims.log
- 标准输出： logs/aims.stdout.log
- 错误日志： logs/aims.stderr.log
- 查看实时日志： tail -f logs/aims.log

常见问题
1. 如果端口 8000 被占用，请修改端口后重启：
   bash start.sh 8080
2. 如果启动失败，请检查 logs 目录下的错误日志。
3. 如果数据采集失败，请检查：
   - 网络连通性（从新加坡访问国内 API 可能有延迟）
   - .env 文件配置是否正确
   - 日志中的 source_errors 字段

反馈问题时请提供
1. 问题描述
2. 操作步骤
3. 实际结果
4. 期望结果
5. 截图或录屏
6. logs 目录
