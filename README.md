---
language:
- en
pipeline_tag: text-generation
tags:
- code
license: apache-2.0
datasets:
- happystar/document-writing-prompts
- happystar/awesome-chatgpt-prompts
---



# **csg-wukong-1B**          [[中文]](#chinese)    [[English]](#english)

<a id="english"></a>

<p align="center">
<img width="300px" alt="OpenCSG" src="https://cdn-uploads.huggingface.co/production/uploads/64c71b27d43e4dee51a8b31a/GwYXPKuEoGCGcMICeW-sb.jpeg">
</p>

<p align="center"><a href="https://portal.opencsg.com/models">[OpenCSG Community]</a>   <a href="https://github.com/opencsgs">[github]</a>  <a href="https://cdn-uploads.huggingface.co/production/uploads/64c71b27d43e4dee51a8b31a/HU6vz21qKTEmUBCWqCFh9.jpeg">[wechat]</a>  <a href="https://twitter.com/OpenCsg">[Twitter]</a> </p>


</div>
OpenCSG stands for Converged resources, Software refinement, and Generative LM. The 'C' represents Converged resources, indicating the integration and full utilization of hybrid resources. The 'S' stands for Software refinement, signifying software that is refined by large models. The 'G' represents Generative LM, which denotes widespread, inclusive, and democratized generative large models.

The vision of OpenCSG is to empower every industry, every company, and every individual to own their models. We adhere to the principles of openness and open source, making the large model software stack of OpenCSG available to the community. We welcome everyone to use, send feedback, and contribute collaboratively.



## Model Description

**csg-wukong-1B** is a 1 billion-parameter small language model(SLM) pretrained on 1T tokens. 
<br>
we will introduce more information about csg-wukong-1B.

## Model Evaluation results

We submitted csg-wukong-1B on the [open_llm_leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard), and
the results show our model ranked the 8th among the ~1.5B pretrained small language models.


![image/png](https://cdn-uploads.huggingface.co/production/uploads/661790397437201d78141856/_HRTxL6N0qnNPNt-P8k9k.png)



# Training

## Hardware

- **GPUs:** 16 H800 
- **Training time:** 43days 

## Software

- **Orchestration:** [Deepspeed](https://github.com/OpenCSGs)
- **Neural networks:** [PyTorch](https://github.com/pytorch/pytorch)
- **BP16 if applicable:** [apex](https://github.com/NVIDIA/apex)


<a id="chinese"></a>

<p>

</p>

# OpenCSG介绍


<p align="center">
<img width="300px" alt="OpenCSG" src="https://cdn-uploads.huggingface.co/production/uploads/64c71b27d43e4dee51a8b31a/GwYXPKuEoGCGcMICeW-sb.jpeg">
</p>

<p align="center"><a href="https://opencsg.com/models">[OpenCSG 社区]</a>   <a href="https://github.com/opencsgs">[github]</a>  <a href="https://cdn-uploads.huggingface.co/production/uploads/64c71b27d43e4dee51a8b31a/HU6vz21qKTEmUBCWqCFh9.jpeg">[微信]</a>  <a href="https://twitter.com/OpenCsg">[推特]</a> </p>



</div>
OpenCSG中 Open是开源开放；C 代表 Converged resources，整合和充分利用的混合异构资源优势，算力降本增效；S 代表 Software refined，重新定义软件的交付方式，通过大模型驱动软件开发，人力降本增效；G 代表 Generative LM，大众化、普惠化和民主化的可商用的开源生成式大模型。

OpenCSG的愿景是让每个行业、每个公司、每个人都拥有自己的模型。 我们坚持开源开放的原则，将OpenCSG的大模型软件栈开源到社区，欢迎使用、反馈和参与共建，欢迎关注。



## 模型介绍


**csg-wukong-1B** 是一个1B参数量的小语言模型，该模型训练了1T tokens.
<br>

我们将在后面介绍更多关于这个模型的信息。


## 模型评测结果

我们把csg-wukong-1B模型提交到[open_llm_leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)榜单上，结果显示我们的模型目前在~1.5B小语言模型中排名第8。


![image/png](https://cdn-uploads.huggingface.co/production/uploads/661790397437201d78141856/ZfWZ1Fd7ccKrJVx0okV9z.png)



# 训练

## 硬件资源

- **GPU数量：** 16 H800 
- **训练时间：** 43天

## 软件使用

- **微调训练框架：** [Deepspeed](https://github.com/OpenCSGs)
- **深度学习框架：** [PyTorch](https://github.com/pytorch/pytorch)
- **BP16：** [apex](https://github.com/NVIDIA/apex)