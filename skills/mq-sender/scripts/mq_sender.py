# -*- coding: utf-8 -*-
import requests
import json
import sys


def smart_serialize(data):
    """
    业务逻辑兼容层：自动处理双重序列化。
    如果发现业务字典中包含特定的 Key（如 dataMap, orderInfos 等），
    且其值为 dict/list 类型，则自动将其序列化为 JSON 字符串。
    """
    # 定义需要被“字符串化”处理的常见业务嵌套字段名
    NESTED_KEYS = ["dataMap", "orderInfos", "ext", "context", "params"]

    if isinstance(data, dict):
        new_data = data.copy()
        for k, v in new_data.items():
            # 命中嵌套字段且当前是对象类型，执行二次序列化
            if k in NESTED_KEYS and isinstance(v, (dict, list)):
                # ensure_ascii=False 确保中文不乱码
                new_data[k] = json.dumps(v, ensure_ascii=False)
            # 递归处理：针对某些三层嵌套的情况进行扫描
            elif isinstance(v, (dict, list)):
                new_data[k] = smart_serialize(v)
        return new_data
    return data


def send_mq_message(cluster_name, queue, payload_dict, reason="Skill-Invoke"):
    """
    通用发送引擎
    """
    url = "http://mqplus.apps01.ali-bj-sit03.shuheo.net/mqplus/amqp/v2/sendMsg"

    # 第一层序列化：处理业务特定的嵌套字段 (如将 dataMap 字典转为字符串)
    processed_payload = smart_serialize(payload_dict)

    # 第二层序列化：网关协议层封装 (将整个业务 Payload 转为字符串)
    gateway_payload = {
        "isAdmin": True,
        "sendType": "Queue",
        "clusterName": cluster_name,
        "queue": queue,
        "reason": reason,
        "msgList": [
            {
                # 这里执行全局序列化
                "payload": json.dumps(processed_payload, ensure_ascii=False)
            }
        ]
    }

    try:
        response = requests.post(url, json=gateway_payload, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            # AI 传入标准 JSON 字典即可，脚本负责处理转义
            args = json.loads(sys.argv[1])
            send_mq_message(
                cluster_name=args.get("cluster_name"),
                queue=args.get("queue"),
                payload_dict=args.get("payload_dict"),
                reason=args.get("reason", "Skill-Invoke")
            )
        except Exception as e:
            print(f"Input Parse Error: {str(e)}")