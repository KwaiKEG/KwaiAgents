<p align="left">
    English ｜ <a href="README_ZH.md">中文</a>
</p>
<br><br>

<p align="center">
    <img src="blob/logo.png" width="400"/>
<p>
<br>

<p align="center">
      📚 <a href="https://huggingface.co/datasets/kwaikeg/KAgentInstruct">Dataset</a> | 📚 <a href="https://huggingface.co/datasets/kwaikeg/KAgentBench">Benchmark</a> | 🤗 <a href="https://huggingface.co/collections/kwaikeg/kagentlms-6551e685b5ec9f9a077d42ef">Models</a> | 📑 <a href="http://arxiv.org/abs/2312.04889">Paper</a>
<br>

KwaiAgents is a series of Agent-related works open-sourced by the [KwaiKEG](https://github.com/KwaiKEG) from [Kuaishou Technology](https://www.kuaishou.com/en). The open-sourced content includes:

1. **KAgentSys-Lite**: a lite version of the KAgentSys in the paper. While retaining some of the original system's functionality, KAgentSys-Lite has certain differences and limitations when compared to its full-featured counterpart, such as: (1) a more limited set of tools; (2) a lack of memory mechanisms; (3) slightly reduced performance capabilities; and (4) a different codebase, as it evolves from open-source projects like BabyAGI and Auto-GPT. Despite these modifications, KAgentSys-Lite still delivers comparable performance among numerous open-source Agent systems available.
2. **KAgentLMs**: a series of large language models with agent capabilities such as planning, reflection, and tool-use, acquired through the Meta-agent tuning proposed in the paper.
3. **KAgentInstruct**: over 200k Agent-related instructions finetuning data (partially human-edited) proposed in the paper.
4. **KAgentBench**: over 3,000 human-edited, automated evaluation data for testing Agent capabilities, with evaluation dimensions including planning, tool-use, reflection, concluding, and profiling.

<table>
    <tr>
        <th>Models</th><th>Training Data</th><th>Benchmark Data</th>
    </tr>
    <tr>
        <td><a href="https://huggingface.co/kwaikeg/kagentlms_qwen_7b_mat">Qwen-7B-MAT</a></td>
        <td align="center" rowspan="2"><a href="https://huggingface.co/datasets/kwaikeg/KAgentInstruct">KAgentInstruct</a></td>
        <td align="center" rowspan="2"><a href="https://huggingface.co/datasets/kwaikeg/KAgentBench">KAgentBench</a></td>
    </tr>
    <tr>
        <td><a href="https://huggingface.co/kwaikeg/kagentlms_baichuan2_13b_mat">Baichuan2-13B-MAT</a></td>
    </tr>
</table>

<br>

<p align="center">
    <img src="blob/example.gif"/>
<p>

<br>

<p align="center">
    <img src="blob/overview.png"/>
<p>

## News
* 2023.1.5 - Training data [[link]](https://huggingface.co/datasets/kwaikeg/KAgentInstruct) released.
* 2023.12.27 - 🔥 KwaiAgents have been reported on many sites. [[机器之心]](https://mp.weixin.qq.com/s/QhZIFL1GHH90z98gnk194g) [[Medium]](https://medium.com/@myscarletpan/can-7b-models-now-master-ai-agents-a-look-at-kwais-recent-llm-open-source-release-8b9e84647412) [[InfoQ]](https://www.infoq.cn/article/xHGJwG3b8hXSdaP4m6r0), etc. 
* 2023.12.13 - The benchmark and evaluation code [[link]](https://huggingface.co/datasets/kwaikeg/KAgentBench) released 
* 2023.12.08 - Technical report [[link]](https://arxiv.org/abs/2312.04889) released
* 2023.11.17 - Initial release

## Evaluation
1. Benchmark Results
   
|                | Scale | Planning | Tool-use | Reflection | Concluding | Profile | Overall Score |
|----------------|-------|----------|----------|------------|------------|---------|---------------|
| GPT-3.5-turbo  |   -   |  18.55   |  26.26   |    8.06    |   37.26    |  35.42  |     25.63     |
| Llama2         |  13B  |   0.15   |   0.44   |    0.14    |   16.60    |  17.73  |      5.30     |
| ChatGLM3       |  6B   |   7.87   |  11.84   |    7.52    |   30.01    |  30.14  |     15.88     |
| Qwen           |  7B   |  13.34   |  18.00   |    7.91    |   36.24    |  34.99  |     21.17     |
| Baichuan2      |  13B  |   6.70   |  16.10   |    6.76    |   24.97    |  19.08  |     14.89     |
| ToolLlama      |  7B   |   0.20   |   4.83   |    1.06    |   15.62    |  10.66  |      6.04     |
| AgentLM        |  13B  |   0.17   |   0.15   |    0.05    |   16.30    |  15.22  |      4.88     |
| Qwen-MAT       |  7B   |  31.64   |  43.30   |   33.34    |   44.85    |  44.78  |     39.85     |
| Baichuan2-MAT  |  13B  |  37.27   |  52.97   |   37.00    |   48.01    |  41.83  |     45.34     |

2. Human evaluation. Each result cell shows the pass rate (\%) and the average score (in parentheses)

|                 | Scale   | NoAgent         | ReACT          | Auto-GPT        | KAgentSys       |
|-----------------|---------|-----------------|----------------|-----------------|-----------------|
| GPT-4           | -       | 57.21% (3.42)    | 68.66% (3.88)   | 79.60% (4.27)    | 83.58% (4.47)    |
| GPT-3.5-turbo   | -       | 47.26% (3.08)    | 54.23% (3.33)   | 61.74% (3.53)    | 64.18% (3.69)    |
| Qwen            | 7B      | 52.74% (3.23)    | 51.74% (3.20)   | 50.25% (3.11)    | 54.23% (3.27)    |
| Baichuan2       | 13B     | 54.23% (3.31)    | 55.72% (3.36)   | 57.21% (3.37)    | 58.71% (3.54)    |
| Qwen-MAT        | 7B      | -                | 58.71% (3.53)   | 65.67% (3.77)    | 67.66% (3.87)    |
| Baichuan2-MAT   | 13B     | -                | 61.19% (3.60)   | 66.67% (3.86)    | 74.13% (4.11)    |


## User Guide

### Prebuild environment
Install miniconda for build environment first. Then create build env first:
```bash
conda create -n kagent python=3.10
conda activate kagent
pip install -r requirements.txt
```

### Using AgentLMs
#### Serving by [vLLM](https://github.com/vllm-project/vllm) (GPU)
We recommend using [vLLM](https://github.com/vllm-project/vllm) and [FastChat](https://github.com/lm-sys/FastChat) to deploy the model inference service. First, you need to install the corresponding packages (for detailed usage, please refer to the documentation of the two projects):
1. For Qwen-7B-MAT, install the corresponding packages with the following commands
```bash
pip install vllm
pip install "fschat[model_worker,webui]"
```
2. For Baichuan-13B-MAT, install the corresponding packages with the following commands
```bash
pip install "fschat[model_worker,webui]"
pip install vllm==0.2.0
pip install transformers==4.33.2
```

To deploy KAgentLMs, you first need to start the controller in one terminal.
```bash
python -m fastchat.serve.controller
```
Secondly, you should use the following command in another terminal for single-gpu inference service deployment:
```bash
python -m fastchat.serve.vllm_worker --model-path $model_path --trust-remote-code
```
Where `$model_path` is the local path of the model downloaded. If the GPU does not support Bfloat16, you can add `--dtype half` to the command line.

Thirdly, start the REST API server in the third terminal.
```bash
python -m fastchat.serve.openai_api_server --host localhost --port 8888
```

Finally, you can use the curl command to invoke the model same as the OpenAI calling format. Here's an example:
```bash
curl http://localhost:8888/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"model": "kagentlms_qwen_7b_mat", "messages": [{"role": "user", "content": "Who is Andy Lau"}]}'
```
Here, change `kagentlms_qwen_7b_mat` to the model you deployed.

#### Serving by [Lamma.cpp](https://github.com/ggerganov/llama.cpp) (CPU)
llama-cpp-python offers a web server which aims to act as a drop-in replacement for the OpenAI API. This allows you to use llama.cpp compatible models with any OpenAI compatible client (language libraries, services, etc). The converted model can be found in [kwaikeg/kagentlms_qwen_7b_mat_gguf](https://huggingface.co/kwaikeg/kagentlms_qwen_7b_mat_gguf).

To install the server package and get started:
```bash
pip install "llama-cpp-python[server]"
python3 -m llama_cpp.server --model kagentlms_qwen_7b_mat_gguf/ggml-model-q4_0.gguf --chat_format chatml --port 8888
```

Finally, you can use the curl command to invoke the model same as the OpenAI calling format. Here's an example:
```bash
curl http://localhost:8888/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"messages": [{"role": "user", "content": "Who is Andy Lau"}]}'
```

### Using KAgentSys-Lite
Download and install the KwaiAgents, recommended Python>=3.10
```bash
git clone git@github.com:KwaiKEG/KwaiAgents.git
cd KwaiAgents
python setup.py develop
```

1. **ChatGPT usage**
Declare some environment variables
```
export OPENAI_API_KEY=sk-xxxxx
export WEATHER_API_KEY=xxxxxx
```

The WEATHER_API_KEY is not mandatory, but you need to configure it when asking weather-related questions. You can obtain the API key from [this website](https://www.weatherapi.com/) (Same for local model usage).

```bash
kagentsys --query="Who is Andy Lau's wife?" --llm_name="gpt-3.5-turbo" --lang="en"
```

2. **Local model usage**
> To use a local model, you need to deploy the corresponding model service as described in the previous chapter
```bash
kagentsys --query="Who is Andy Lau's wife?" --llm_name="kagentlms_qwen_7b_mat" \
--use_local_llm --local_llm_host="localhost" --local_llm_port=8888 --lang="en"
```


Full command arguments:

```
options:
  -h, --help            show this help message and exit
  --id ID               ID of this conversation
  --query QUERY         User query
  --history HISTORY     History of conversation
  --llm_name LLM_NAME   the name of llm
  --use_local_llm       Whether to use local llm
  --local_llm_host LOCAL_LLM_HOST
                        The host of local llm service
  --local_llm_port LOCAL_LLM_PORT
                        The port of local llm service
  --tool_names TOOL_NAMES
                        the name of llm
  --max_iter_num MAX_ITER_NUM
                        the number of iteration of agents
  --agent_name AGENT_NAME
                        The agent name
  --agent_bio AGENT_BIO
                        The agent bio, a short description
  --agent_instructions AGENT_INSTRUCTIONS
                        The instructions of how agent thinking, acting, or talking
  --external_knowledge EXTERNAL_KNOWLEDGE
                        The link of external knowledge
  --lang {en,zh}        The language of the overall system
  --max_tokens_num      Maximum length of model input
```

**Note**:
1. If you need to use the `browse_website` tool, you need to configure the [chromedriver](https://chromedriver.chromium.org/getting-started) on your server.
2. If the search fails multiple times, it may be because the network cannot access duckduckgo_search. You can solve this by setting the `http_proxy`.


### Using KAgentBench Evaluation
We only need two lines to evaluate the agent capabilities like:
```bash
cd benchmark
python infer_qwen.py qwen_benchmark_res.jsonl
python benchmark_eval.py ./benchmark_eval.jsonl ./qwen_benchmark_res.jsonl
```
The above command will give the results like
```
plan : 31.64, tooluse : 43.30, reflextion : 33.34, conclusion : 44.85, profile : 44.78, overall : 39.85
```

Please refer to <a href="benchmark/">benchmark</a> for more details.

## Citation
```
@article{pan2023kwaiagents,
  author    = {Haojie Pan and
               Zepeng Zhai and
               Hao Yuan and
               Yaojia Lv and
               Ruiji Fu and
               Ming Liu and
               Zhongyuan Wang and
               Bing Qin
               },
  title     = {KwaiAgents: Generalized Information-seeking Agent System with Large Language Models},
  journal   = {CoRR},
  volume    = {abs/2312.04889},
  year      = {2023}
}
```
