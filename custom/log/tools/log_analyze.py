#!/usr/bin/env python3
# -*- coding:utf-8 -*-
### 日志格式化解析工具

import re

from custom.log.lib.filter import Filter
from custom.log.lib.log import LogType, Log, LogStatus
from custom.log.lib.tree_data import write_head, write_end, write_records


def match_log_start(log):
    pattern = r'(^\d{4}[\D]\d{1,2}[\D]\d{1,2} \d{2}:\d{2}:\d{2}[\D]\d{3} (DEBUG|INFO|ERROR|WARN) )'
    return re.search(pattern, log)


def match_log(log_type, keyword):
    for idx in range(len(trace_logs) - 1, -1, -1):
        if trace_logs[idx].type == log_type and trace_logs[idx].keyword == keyword:
            return idx
    return None


if __name__ == '__main__':
    trace_logs = []
    last_log = None

    log_filter = Filter("/Users/defu/Downloads/test.log",
                        "f950df6af0ad3adfbcb9613a83cf1f8d")
    log_filter.filter()
    for line in log_filter.lines:
        is_new_log = match_log_start(line)
        if is_new_log:
            # 新 log 行
            log = Log(line, "")
            if log.type == LogType.Unknown:
                continue
            if last_log is None:
                print("新请求")
                last_log = log
                trace_logs.append(last_log)
            else:
                log = Log(line, "")
                # 新span有三种可能性：1. 进入孩子节点；2. 进入兄弟节点；3. 回到父亲节点
                # 1. 进入孩子节点: 当前节点status未到End
                # 2. 进入兄弟节点：当前节点status为End，新节点和当前节点span_id相同
                # 3. 回到父亲节点：当前节点status为End，新节点和当前节点span_id不同
                if log.span_id != last_log.span_id:
                    if last_log.status != LogStatus.End:
                        # 进入孩子节点: 当前节点status未到End
                        print("进入孩子节点")
                        log.p_span_id = last_log.span_id
                        last_log = log
                        trace_logs.append(last_log)
                    else:
                        # 回到父亲节点：当前节点status为End，新节点和当前节点span_id不同
                        # 当前节点是上一个节点的父节点
                        print("回到父亲节点")
                        last_log.p_span_id = log.span_id
                        idx = match_log(log.type, log.keyword)
                        if idx is not None:
                            trace_logs[idx].response = log.response
                else:
                    # 进入兄弟节点：当前节点status为End，新节点和当前节点span_id相同
                    print("进入兄弟节点")
                    log.p_span_id = last_log.p_span_id
                    last_log = log
                    trace_logs.append(last_log)
        elif last_log.type == LogType.Error:
            # 原log，新行，如 error log
            last_log.content = last_log.content + line + "\n"

    fo = write_head("test_tree_data")
    if len(trace_logs) > 0:
        write_records(fo, trace_logs, True)
    write_end(fo)
