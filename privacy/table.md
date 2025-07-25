```
\begin{table*}[!t]
    \centering
    \footnotesize
    \caption{List of the Collected Syntax Conventions (\texttt{[SP]}, \texttt{BR}, and \texttt{[IND]} denote the space, line break, and indentation, respectively.)}\label{table:syntax}
    \vspace{-10pt}
    \begin{tabular}{m{2.8cm}m{2cm}m{4cm}m{6cm}}
        \toprule
        \textbf{Category} &\textbf{Syntax Node}  & \textbf{Conditional Token} & \textbf{Consequent Token} \\
        \midrule
        
        \multirow{7}{*}{Data Model}  & Lists & `[' & `]' \\
        \cmidrule{2-4}
            & Dict &  `\{' & `\}' \\
            \cmidrule{2-4}
            & String/bytes  & ``',`"' &   `'',`"'  \\
            \cmidrule{2-4}
            & Object & \textit{identifier} & `.' \\
            \cmidrule{2-4}
            & Tuple & `(' & `)' \\
            \cmidrule{2-4}
            & Set &  `\{' & `\}' \\
            \cmidrule{2-4}
            & Slice &  `[' & `]' \\\hline
        \multirow{5}{*}{Expressions} & call & \textit{identifier}( & `)' \\
        \cmidrule{2-4}
            & lambda & \texttt{lambda} \textit{params} & `:' \\
        \cmidrule{2-4}
            & comprehension & \textit{expr} \texttt{for} \textit{target} & \texttt{in}, `]', `\}', `)'  \\
        \cmidrule{2-4}
            & conditional & \textit{expr} \texttt{if} \textit{cond} & \texttt{else} \\
        \cmidrule{2-4}
            & \shortstack{Chained\\Comparison} & \textit{expr comp\_op expr} & \textit{comp\_op} \\\hline
        \multirow{4}{*}{Single Statements} 
        & \texttt{import} & \texttt{import} \textit{module}  & \texttt{as} \\
        \cmidrule{2-4}
        & \texttt{from-import} & \texttt{from} \textit{module} & \texttt{import} \\
        \cmidrule{2-4}
        & \texttt{assert} & \texttt{assert} \textit{test} & `,', \textit{msg} \\
        \cmidrule{2-4}
        & \shortstack{Scope\\Declaration} & \texttt{global}/\texttt{nonlocal} & \textit{identifier}, `,' \\
        \hline
        \multirow{15}{*}{Compound Statements} 
        & \texttt{if} & \texttt{if} \textit{assignment\_expression} & `:', \texttt{[SP]}, \texttt{[BR]}, \texttt{[IND]}, \texttt{elif}, \texttt{else}\\
        \cmidrule{2-4}
        & \texttt{for}   & \texttt{for} \textit{target\_list}  & \texttt{in}, `:', \texttt{[SP]}, \texttt{[IND]},  \texttt{[BR]} \\
        \cmidrule{2-4}
        & \multirow{2}{*}{\texttt{try}} &  \texttt{try} &  `:', \texttt{[SP]},  \texttt{BR}, \texttt{[IND]}, \texttt{except}, \texttt{except*},\texttt{finally}, \texttt{else} \\
        \cmidrule{3-4}
        &    & \texttt{except} \textit{expression}  &  \texttt{as},  `:', \texttt{[SP]}, \texttt{[BR]}, \texttt{[IND]} \\
        \cmidrule{2-4}
        & \texttt{with} & \texttt{with} \textit{with\_stmt\_contents}  & \texttt{as}, `:', \texttt{[SP]}, \texttt{[BR]}, \texttt{[IND]} \\
        \cmidrule{2-4}
        & \multirow{2}{*}{\texttt{class}}  & \texttt{class} \textit{classname} & `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]} \\
        \cmidrule{3-4}
        & & \texttt{class} \textit{classname}(\textit{identifier}) &  `,', `)', `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]}  \\
        \cmidrule{2-4}
        & \multirow{3}{*}{function} & \texttt{def} \textit{funcname}( & \texttt{self}, `/', `*', `)' \\
        \cmidrule{3-4}
        & & \texttt{def} \textit{funcname}(\textit{identifier}) & `,` \\
        \cmidrule{3-4}
        & & \texttt{def} \textit{funcname}(...) & `->`, `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]} \\
        \cmidrule{2-4}
        & \texttt{while} & \texttt{while} \textit{condition} & `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]}, \texttt{else}\\
        \cmidrule{2-4}
        & \texttt{match} & \texttt{match} \textit{subject} & \texttt{case}, `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]} \\
        \cmidrule{2-4}
        & \texttt{async def} & \texttt{async def} \textit{funcname}(...) & `)', `:', \texttt{[SP]}, \texttt{[IND]}, \texttt{[BR]} \\
        \cmidrule{2-4}
        & \texttt{async for} & \texttt{async for} \textit{target\_list}  & \texttt{in}, `:', \texttt{[SP]}, \texttt{[IND]},  \texttt{[BR]} \\
        \cmidrule{2-4}
        & \texttt{async with} & \texttt{async with} \textit{expr}  & \texttt{as}, `:', \texttt{[SP]}, \texttt{[BR]}, \texttt{[IND]} \\
        \bottomrule
    \end{tabular}
\end{table*}
```

