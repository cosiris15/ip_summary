# IP 合同梳理后端（LLM 版）

本项目提供后端流水线：识别合同方向（上游/下游）、按表头调用 LLM 提取字段、生成可人工校对的 JSON 中间结果，并汇总为 CSV/Excel 以便入库或前端对接。

## 环境准备
- 复制 `config/deepseek_config.example.yaml` 为 `config/deepseek_config.yaml`，填入 DeepSeek `api_key`（或通过环境变量 `DEEPSEEK_API_KEY` 设置）。
- 安装依赖：`pip install -r requirements.txt`

## 核心命令
- 运行合同处理（分类 + 提取，生成 JSON 中间结果）：
  ```bash
  python main.py run --my-party "深圳腾讯" \
    --input-dir 合同样例 \
    --intermediate-dir output/intermediate \
    [--force-direction upstream|downstream]  # 可选，强制方向
  ```
- 汇总用户校对后的 JSON 为 CSV/Excel，并追加历史：
  ```bash
  python main.py aggregate --direction upstream \
    --intermediate-dir output/intermediate \
    --final-dir output/final \
    --history-dir output/history
  ```
  `--direction downstream` 处理下游合同；默认输出名为 `{direction}_YYYYMMDD_HHMMSS.*`。

## 数据流
1) 用户把合同文件放到输入目录（默认 `合同样例/`），指定“我方”主体。
2) `run`：对每份合同调用 DeepSeek 判定方向，再用对应表头 prompt 提取字段，结果写入 `output/intermediate/{upstream,downstream}/*.json`，便于人工修改。
3) 用户在 JSON 中直接改字段值（保持键不变）。
4) `aggregate`：读取 JSON，生成 CSV/Excel 到 `output/final/`，同时把结果追加到 `output/history/{direction}_history.csv`。

## 结构说明
- `src/ip_summary/config.py`：加载 YAML 配置，支持 `DEEPSEEK_API_KEY` 覆盖。
- `src/ip_summary/document_loader.py`：读取 md/txt/docx/pdf 合同文本。
- `src/ip_summary/prompts.py`：分类与提取的 prompt 模板（v1.0）。
- `src/ip_summary/pipeline.py`：主流程、并发 LLM 调用、生成中间/汇总结果。
- `src/ip_summary/storage.py`：表头读取、JSON 读写、汇总导出。

## 提示词要点
- 分类：依据“我方”主体判定“我们取得权利/委托创作”为上游，“我们向外授权/转让”为下游，输出 JSON。
- 提取：严格使用表头字段名作为 JSON key，未提及字段填 `null`，多值用 `、` 连接，优先 `YYYY-MM-DD` 日期格式。

## 补充
- 默认表头文件使用 `表头字段/版权授权链-上游类-表头信息.xlsx` 与 `表头字段/版权授权链-下游类-表头信息.xlsx`，可通过 CLI 覆盖。
- 并发请求默认 3，可通过 `--concurrency` 调整以控制速率/成本。

## Web 前端 + API（FastAPI）
- 启动后端 API（含静态前端）：  
  ```bash
  uvicorn api_server:app --reload --port 8000
  ```  
  访问 `http://127.0.0.1:8000/` 打开前端页面。

- 前端功能：新建任务→上传合同→一键运行 LLM→上下游结果分表展示→在线修改单元格→确认入库（生成 CSV/Excel 并写入 history）。

- API 关键接口（部分）：
  - `POST /tasks?name=任务名&my_party=我方主体` 新建任务；
  - `POST /tasks/{task_id}/upload` 上传多个文件（multipart）；
  - `POST /tasks/{task_id}/run` 运行 LLM 流程（支持 query: `force_direction=upstream|downstream` 强制方向）；
  - `GET /tasks/{task_id}/results?direction=upstream|downstream` 拉取中间结果；
  - `PATCH /tasks/{task_id}/results/{direction}/{filename}` 在线修改字段；
  - `POST /tasks/{task_id}/results/move` 调整方向（上/下游互相移动，便于人工 override）；
  - `POST /tasks/{task_id}/finalize` 入库生成 CSV/Excel。
  - `GET /tasks/{task_id}/final/{direction}/{fmt}` 下载最新 CSV/Excel；`GET /tasks/{task_id}/final/archive` 打包下载全部。

- 任务数据存放在 `tasks/{task_id}/`（input/intermediate/final），如需清理可删除对应子目录。
