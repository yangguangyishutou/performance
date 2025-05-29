### 1.benchmark：600个项目分长度的分法描述

在草稿上修改：

```latex
\textbf{Length.} We define the length of a code snippet as the number of lines of code (LOC). We divide the LOC into three categories: short (1-10 LOC), medium (11-50 LOC), and long (51+ LOC).
```



### 2.benchmark：python如何构建

```latex
\textbf{Members.} We refer to the Pile dataset which was used as the pre-training corpora for a number of models. Specifically, we select the first \todo{XXX} projects in the official code dataset document in order. Next, we collected a total of \todo{300} Python files (\eg~\texttt{.py}) from the \todo{XXX} projects, excluding testing files. It totals \todo{XXX} Python functions.
  

\textbf{Non-members.}  Select Python repositories released after 2024 year 1 month on GitHub to ensure that these codes have not been seen during model training. Then sort them in descending order by the number of stars, and filter projects containing \todo{XXX}-\todo{XXX} Python functions one by one to ensure the quality of the samples. Finally, select \todo{300} projects as the negative sample set.
```





### 3.benchmark详细信息填空

```latex
\begin{table}[!t] 
    \centering
    \caption{Benchmark Statistics}\label{tab:benchmark}
    \begin{tabular}{m{2cm}m{2.2cm}m{1cm}m{1cm}m{1cm}m{1cm}m{0.8cm}m{0.8cm}m{0.8cm}}
    \toprule
    \multirow{2}{*}{Language}  &  \multirow{2}{*}{Label}  & Proj. (\#) & Files (\#)  & Func. (\#) & LOC (\#)  & \multicolumn{3}{c}{Length}  \\ 
     \cmidrule(lr){7-9}       
    &  & & & & & Short & Mid & Long \\
    \midrule
    \multirow{2}{*}{Python} & Members & & & & & \\
    & Non-Members & & & & & \\\hline
    \multirow{2}{*}{Java} & Members & & & & & \\
    & Non-Members & & & & & \\
    \bottomrule
    \end{tabular}
\end{table}
```



### 4.结果表格填空

```latex
\begin{table}[!t] 
\centering
\caption{Comparison of methods across different models with AUROC scores (\%)}\label{tab:main_results}
\begin{tabular}{m{2cm}m{2.6cm}m{1.8cm}m{1.8cm}m{1.8cm}m{1.8cm}}
\toprule
\textbf{Language} &\textbf{Method} & \textbf{Pythia-2.8B} & \textbf{Pythia-12B} & \textbf{GPT-Neo-2.7B} & \textbf{StableLM-Alpha-3B}\\
\midrule

\multirow{6}{*}{Python} & Loss & 37.1 & 59.5 & 29.2 & 33.9 \\
&ZLib & 31.5 & 32.6 & 29.3 & 31.0 \\
&Min-K Prob & 39.2  & 57.9  & 31.2  & 34.4  \\ % K=0.2
&\textsc{Gotcha} & & & &\\
&\textsc{DC-PDD} & & & &\\\cmidrule{2-6}
&\tool-0.1 & 56.3 & 51.9  & 51.8 & 52.7  \\\hline

\multirow{6}{*}{Java} & Loss & 37.1 & 59.5 & 29.2 & 33.9 \\
&ZLib & 31.5 & 32.6 & 29.3 & 31.0 \\
&Min-K Prob & 39.2  & 57.9  & 31.2  & 34.4  \\ % K=0.2
&\textsc{Gotcha} & & & &\\
&\textsc{DC-PDD} & & & &\\\cmidrule{2-6}
&\tool-0.1 & 56.3 & 51.9  & 51.8 & 52.7  \\
\bottomrule
\end{tabular}
\end{table}




\begin{table}[!t] 
    \centering
    \caption{AUROC Score of \tool under Different Lengths}
    \begin{tabular}{m{2cm}m{2cm}m{1.8cm}m{1.8cm}m{1.8cm}m{1.8cm}}
    \toprule
    \textbf{Language} &\textbf{Length} & \textbf{Pythia-2.8B} & \textbf{Pythia-12B} & \textbf{GPT-Neo-2.7B} & \textbf{StableLM-Alpha-3B}\\
    \midrule
    \multirow{3}{*}{Python} & Short & & & & \\
     & Mid & & & & \\
    &High & & & & \\
    \hline
    \multirow{3}{*}{Java} & Short & & & & \\
     & Mid & & & & \\
    &High & & & & \\
    \bottomrule
    \end{tabular}
    \label{tab:main_results}
\end{table}
```

