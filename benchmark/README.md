
KAgentBench is the benchmark proposed in KwaiAgents ([Github](https://github.com/KwaiKEG/KwaiAgents)), which is a series of Agent-related works open-sourced by the [KwaiKEG](https://github.com/KwaiKEG) from [Kuaishou Technology](https://www.kuaishou.com/en). It contains over 3,000 human-edited, automated evaluation data for testing Agent capabilities, with evaluation dimensions including planning, tool-use, reflection, concluding, and profiling.


## Overall statistics of KAgentBench
---

| type| #Queries | #Inst | Avg. #Ground | Avg. #Tools | Avg. #Turns | Avg. #Tasks | Avg. Len-Know | Metric |
| :-------: | :-------:| :-------: | :-------: | :-------: | :-------: | :-------: | :-------: | :-------: |
| Planning & Tool-use  |  320   |  1,317  |  4.12 |  8.68 |  1.51  |  2.21 |  245.31 |  ROUGE-L, EM |
| Reflection  |  68   |  272  |  4 |  12 |  1 |  3.97 |  1369.04 |  ROUGE-L, EM |
| Concluding  |  245   |  1,225 |  5 |  - |  1.52 |  2.14 |  923.96 |  ROUGE-L |
| Profile  |  433   |  433 |  5 |  - |  1.99 |  - |  - |  ROUGE-L |




##  Experimental results of different LLMs on KAgentBench
---
The specific performance of different models on benchmarks can be seen in more detail in our [paper](https://arxiv.org/abs/2312.04889).

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



## JSON Format
---

Each data point is
a dict with the following keys:
- `id`: a unique id for this data point. This is useful for evaluation.
- `query`: a string.
- `type`: a string, the type of this data(plantooluse,reflextion,conclusion,profile).
- `golden_result_list`: a list. The reference response.
- `funcs`: a list of functions that may be used in the current query
- `prompt_input`: a dict,input composed of different prompt templates
- `memory`: a string
- `memory_type`: a string,types of memory: task, knowledge, conversation
- `memory_last_task`: a list, in the case where memory is task, the last task information in the previous round

The overall data format is as follows
```json
{
  "id": "",
  "query": "",
  "type": "",
  "golden_result_list": [],
  "funcs": [],
  "prompt_input": {},
  "memory": "",
  "memory_type": "",
  "memory_last_task": {}
}
```

## How to download benchmark
---

You can download the benchmark evaluation set through [kwaikeg/KAgentBench](https://huggingface.co/datasets/kwaikeg/KAgentBench/tree/main), or you can also download the benchmark evaluation set on [KwaiAgents](https://github.com/KwaiKEG/KwaiAgents).
The filename of the evaluation set is 'benchmark_eval.jsonl'. Download the file to your local system.

## Environment Setup
---

Please make sure you have setup the environment and installed the required packages. Make sure you meet the above requirements, and then install the dependent libraries.
```bash
pip install -r requirements.txt
```

## Benchmark Inference
To run benchmark evaluations using different models, it is necessary to appropriately load and predict according to the model in the inference script. Different models may have variations in their initialization and loading methods. We have provided inference scripts for both the Qianwen and Baichuan models. Inference for other models can be adapted based on the scripts we have provided.
Taking the provided open-source model kagentlms_qwen_7b_mat as an example.（The kagentlms_qwen_7b_mat model has been uploaded to [huggingface](https://huggingface.co/kwaikeg/kagentlms_qwen_7b_mat)）
Run the script to perform benchmark predictions. The parameter is the prediction results file.
```bash
python infer_qwen.py qwen_benchmark_res.jsonl
```
Similarly, to perform evaluations using the 'kagentlms_baichuan2_13b_mat' model, execute the following command.
```bash
python infer_baichuan.py baichuan_benchmark_res.jsonl
```
The prediction results will be stored in the 'model_predict' field, which is a dictionary (dict) structure. The key is the type of prompt, and the corresponding value is the output of the model. In the 'profile', as it contains only one prompt, 'model_predict' is a string, and the corresponding value is the model output.

Below is an example display of a prediction result for 'conclusion' data.
```json
{
  "query": "在过去的一年中，哪个月份的全球气温最高？",
  "id": "0ae75cf4-8897-5998-b74c-c7ae7202621c",
  "type": "conclusion",
  "memory_type": "task",
  "memory": "...",
  "funcs": [],
  "memory_last_task": {},
  "golden_result_list": [
    "2022年中，6月是全球最高气温。",
    "2022年中，全球最高气温是6月。",
    "2022年中，全球最高气温是6月。",
    "2022年中，6月是全球最高气温。",
    "2022年中，全球最高气温是6月。"
  ],
  "prompt_input": {...},
  "model_predict": {
    "ReACT": "2022年7月的全球气温最高，达到了17.23℃。",
    "AutoGPT": "在过去的一年中，全球气温最高的月份是2023年4月，全球表面平均气温达到了17.23°C，创下了历史新高。这一数据来自于美国国家海洋和大气管理局与美国缅因大学汇编的初步数据。",
    "ModelScope": "在过去一年中，全球气温最高的月份是2023年7月。根据美国国家航空航天局（NASA）和美国国家海洋和大气管理局（NOAA）的最新研究报告，2022年是史上排名第6的最热年份，尽管拉尼娜现象改变了天气模式，抑制了全球气温。然而，2023年7月的全球平均气温达到了17.23℃，超过了7月4日和5日创下的17.18℃的联合纪录，而后者之前曾打破了7月3日创下的17.01℃的纪录。",
    "ToolLlama": "Thought: I have found the information about the warmest month in 2022 in the memory. I will use this information to answer the question and call the Finish function to provide the final answer.\nAction: Finish\nAction Input: {\"return_type\": \"give_answer\", \"final_answer\": \"在2022年，全球最暖的月份是5月，比20世纪平均值高出1.39°F（0.77°C）。\"}",
    "Kuaiagent": "在过去的一年中，全球气温最高的月份是2023年7月。根据美国国家航空航天局（NASA）和美国国家海洋和大气管理局（NOAA）的最新研究报告，2023年7月的全球平均气温达到了17.23℃，超过了19世纪50年代有仪器记录以来的任何一个月。"
  }
}
```
'...' indicates that the content is too extensive. For the sake of convenient display format, the content has been abbreviated.






## Evaluation
Taking the inference results of the 'kagentlms_qwen_7b_mat' model as an example, calculate the metrics based on the benchmark inference results obtained from the 'infer'. Execute the following command to get the overall score.

The first parameter is the benchmark evaluation set, which contains reference responses manually annotated, and the second parameter is the prediction results of the model being evaluated.
```bash
python benchmark_eval.py ./benchmark_eval.jsonl ./qwen_benchmark_res.jsonl
```
The final model score is as follows:
```bash
plan : 31.64, tooluse : 43.30, reflextion : 33.34, conclusion : 44.85, profile : 44.78, overall : 39.85
```

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