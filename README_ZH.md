<p align="left">
    <a href="README.md">English</a> ｜ 中文
</p>
<br><br>

<p align="center">
    <img src="blob/logo.png" width="400"/>
<p>
<br>

<p align="center">
      📚 <a href="https://huggingface.co/datasets/kwaikeg/KAgentInstruct">Dataset</a> | 📚 <a href="https://huggingface.co/datasets/kwaikeg/KAgentBench">Benchmark</a> |🤗 <a href="https://huggingface.co/collections/kwaikeg/kagentlms-6551e685b5ec9f9a077d42ef">Models</a> | 📑 <a href="https://arxiv.org/">Paper</a>
<br>


KwaiAgents 是[快手快知团队](https://github.com/KwaiKEG)开源的一整套Agent系列工作。开源的内容包括
1. **KAgentSys-Lite**：基于开源的搜索引擎、浏览器、时间、日历、天气等工具实现的实验级Agent Loop，比较论文中的系统仅缺失记忆机制、以及部分搜索能力
2. **KAgentLMs**：经过论文中提出的Meta-agent tuning过后，具有Agents的规划、反思、工具使用等能力的系列大模型
3. **KAgentInstruct**：论文中Meta-agent生成的指令微调数据
4. **KAgentBench**：>三千条经人工编辑的自动化评测Agent能力数据，能力评测维度包含规划、工具使用、反思、总结、人设指令等


<table>
    <tr>
        <th>模型</th><th>训练数据</th><th>Benchmark</th>
    </tr>
    <tr>
        <td><a href="https://huggingface.co/kwaikeg/kagentlms_qwen_7b_mat">Qwen-7B-MAT</a></td>
        <td align="center" rowspan="2"><a href="https://huggingface.co/datasets/kwaikeg/KAgentInstruct">KAgentInstruct</a><p>(upcoming)</p></td>
        <td align="center" rowspan="2"><a href="https://huggingface.co/datasets/kwaikeg/KAgentBench">KAgentBench</a><p>(upcoming)</p></td>
    </tr>
    <tr>
        <td><a href="https://huggingface.co/kwaikeg/kagentlms_baichuan2_13b_mat">Baichuan2-13B-MAT</a></td>
    </tr>
</table>

<br>

<p align="center">
    <img src="blob/overview.png"/>
<p>

## 使用指南

### AgentLMs 系列模型使用
我们建议用[vLLM](https://github.com/vllm-project/vllm)和[FastChat](https://github.com/lm-sys/FastChat)来部署模型推理服务，首先需要安装对应的包(详细使用请参考两个项目对应文档)：
1. 对于 Qwen-7B-MAT，按如下方法安装
```bash
pip install vllm
pip install "fschat[model_worker,webui]"
```
1. 对于 Baichuan-13B-MAT，按如下方法安装
```bash
pip install "fschat[model_worker,webui]"
pip install vllm==0.2.0
pip install transformers==4.33.2
```

为了能够部署KAgentLMs系列模型，首先需要在一个终端开启controler
```bash
python -m fastchat.serve.controller
```
然后，再在另一个终端开启单卡模型推理服务部署
```bash
python -m fastchat.serve.vllm_worker --model-path $model_path --trust-remote-code
```
其中`$model_path`为从huggingface中下载的模型本地路径，如果显示GPU不支持Bfloat16，可以再命令行后再加个`--dtype half`。
然后，在第三个终端上开启REST API服务器
```bash
python -m fastchat.serve.openai_api_server --host localhost --port 8888
```

最后你就可以用curl命令对应OpenAI调用格式进行模型调用啦，参考示例：
```bash
curl http://localhost:8888/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"model": "kagentlms_qwen_7b_mat", "messages": [{"role": "user", "content": "刘德华是谁"}]}'
```
这里 `kagentlms_qwen_7b_mat` 要改成你部署的模型。


### KAgentSys-Lite 快速使用
下载并安装环境包，建议Python>=3.10
```bash
git clone git@github.com:KwaiKEG/KwaiAgents.git
cd KwaiAgents
python setup.py develop
```

1. **ChatGPT调用**
声明一些环境变量
```
export OPENAI_API_KEY=sk-xxxxx
export WEATHER_API_KEY=xxxxxx
```

其中WEATHER_API_KEY不是必须，但问到天气相关的问题时需要进行配置，APIKEY可以从[这个网站](https://www.weatherapi.com/)中获取（本地模型调用同）。

```bash
kagentsys --query="刘德华老婆是谁？" --llm_name="gpt-3.5-turbo" --lang="zh"
```

1. **本地模型调用**
> 调用本地模型需要参考上一章部署对应模型服务
```bash
kagentsys --query="刘德华老婆是谁？" --llm_name="kagentlms_qwen_7b_mat" \
--use_local_llm --local_llm_host="localhost" --local_llm_port=8888 --lang="zh"
```

下面是完整的命令行参数

| 参数名 | 类型 | 默认值 | 描述 |
| ----- | ---- | ------ | --- |
| --id | str | test | 对话的ID |
| --query | str |  | 用户查询问题 |
| --history | str | [] | 对话历史 |
| --llm_name | str | gpt-3.5-turbo | LLM的名称 |
| --use_local_llm | str | False | 是否使用本地LLM |
| --local_llm_host | str | localhost | 本地LLM部署的IP |
| --local_llm_port | int | 8888 | 本地LLM部署的端口 |
| --tool_names | str | ["auto"] | 使用工具的列表，可选有 web_search,browse_website,get_weather_info,get_calendar_info,time_delta,get_solar_terms_info |
| --max_iter_num | int | 1 | agent迭代次数 |
| --agent_name | str |  | agent名称 |
| --agent_bio | str |  | agent简介，简短的描述 |
| --agent_instructions | str | | agent的指导原则，描述agent如何思考、行动、或交流 |
| --external_knowledge | str |  | 外部知识链接 |
| --language | str | en | 系统的语言，可选（英语/中文） |

**提示**：
1. 如果需要用到 browse_website 工具，需要在服务器上配置[chromedriver](https://chromedriver.chromium.org/getting-started)
2. 如果多次显示搜索失败，可能是网络无法访问duckduckgo_search，可以通过设置`http_proxy`解决
