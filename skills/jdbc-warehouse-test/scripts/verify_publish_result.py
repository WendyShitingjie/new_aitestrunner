#!/usr/bin/env python3
"""
批量入仓发布结果验证脚本
执行 TKR_007 规则：验证��量入仓任务是否完整发布成功
"""
import mysql.connector
import sys
import time
import configparser
import os


def load_db_config(config_file='../../test-table/scripts/db_config.ini', env='bigdata-biz-dataops'):
    """
    加载数据库配置

    Args:
        config_file: 配置文件路径
        env: 环境名称

    Returns:
        dict: 数据库配置
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')

    if env not in config:
        raise ValueError(f"环境 '{env}' 不存在于配置文件中")

    db_config = {
        'host': config[env]['host'],
        'port': int(config[env]['port']),
        'database': config[env]['database'],
        'user': config[env]['username'],
        'password': config[env]['password'],
        'charset': 'utf8mb4'
    }

    return db_config


def verify_publish_result(table_name, instance_name, db_name, timeout=360):
    """
    轮询验证批量入仓任务是否发布成功（支持 6 分钟超时控制）

    修复说明：
    - 开启 conn.autocommit = True，解决 MySQL 可重复读隔离级别导致的快照数据不一致问题。
    - 逻辑：状态 = 7 继续轮询，状态 = 0 验证成功，超时则验证失败。
    """
    print("=" * 60)
    print("批量入仓发布结果验证（TKR_007 - 实时轮询版）")
    print("=" * 60)
    print(f"表名: {table_name}")
    print(f"实例名: {instance_name}")
    print(f"数据库名: {db_name}")
    print(f"最大等待时间: {timeout} 秒")
    print("=" * 60)

    start_time = time.time()
    query_interval = 15  # 每 15 秒查询一次数据库

    try:
        # 1. 加载配置并连接数据库
        db_config = load_db_config()
        conn = mysql.connector.connect(**db_config)

        # ⭐ 核心修复：开启自动提交模式
        # 这样每次 cursor.execute 都会看到数据库中其他事务已提交的最新更改
        conn.autocommit = True

        cursor = conn.cursor(dictionary=True)

        sql = """
        SELECT
            ds.id AS datasource_config_id,
            ds.table_name,
            ds.instance_name,
            ds.db_name,
            ds.status AS datasource_status,
            node.id AS node_config_id,
            node.extract_method,
            node.deal_method,
            sch.id AS schedule_config_id,
            sch.scheduling_cycle,
            sch.scheduling_time,
            pi.id AS process_instance_id,
            pi.status AS process_status,
            pi.start_time,
            pi.end_time
        FROM dataops_extract_input_datasource_config_info ds
        INNER JOIN dataops_extract_node_config_info node
            ON ds.id = node.extract_input_datasource_config_id
        INNER JOIN dataops_task_schedule_config_info sch
            ON node.extract_schedule_config_id = sch.id
        LEFT JOIN dataops_process_instance_info pi
            ON node.id = pi.process_business_id
        WHERE ds.table_name = %s
          AND ds.instance_name = %s
          AND ds.db_name = %s
          AND ds.status = 0
        """

        results = []
        is_published = False

        # 2. 开始实时轮询
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)

            cursor.execute(sql, (table_name, instance_name, db_name))
            results = cursor.fetchall()

            if not results:
                print(f"⏳ [{elapsed}s] 数据库中尚未生成配置记录，继续等待...")
            else:
                # 获取最新的 process_status
                current_status = results[0]['process_status']

                if current_status == 0:
                    print(f"✅ [{elapsed}s] 实时检测到 process_status = 0，发布任务已完成！")
                    is_published = True
                    break
                elif current_status == 7:
                    print(f"⏳ [{elapsed}s] 实时检测到 process_status = 7 (发布中)，继续等待状态流转...")
                else:
                    # 如果状态既不是 7 也不是 0，打印出来以便观察是否有其他异常状态
                    print(f"ℹ️ [{elapsed}s] 当前数据库状态值为: {current_status}，继续监测...")

            # 3. 等待间隔
            time.sleep(query_interval)

        # 4. 超时判断
        if not is_published:
            print(f"\n❌ 验证失败：在 {timeout} 秒内任务状态未变为 0 (任务可能卡在状态 7 或发布异常)")
            cursor.close()
            conn.close()
            return False

        # 5. 详细字段断言验证 (只有状态为 0 才会走到这里)
        print("\n" + "=" * 60)
        print("状态已就绪，开始执行字段级详细断言")
        print("=" * 60)
        print(f"✅ 记录总数: {len(results)}\n")

        success_count = 0
        for idx, row in enumerate(results, 1):
            print(f"检查记录 {idx}:")
            print(
                f"  [ID验证] 数据源配置: {row['datasource_config_id']} | 节点配置: {row['node_config_id']} | 调度配置: {row['schedule_config_id']}")
            print(f"  [状态验证] 流程状态: {row['process_status']}")

            assertions_passed = True

            # 验证各表关联 ID 是否成功生成（非空）
            if not row['node_config_id']:
                print("  ❌ 异常：抽数节点配置 ID 为空")
                assertions_passed = False
            if not row['schedule_config_id']:
                print("  ❌ 异常：任务调度配置 ID 为空")
                assertions_passed = False
            if not row['process_instance_id']:
                print("  ❌ 异常：流程实例 ID 为空")
                assertions_passed = False

            if assertions_passed:
                print("  ✅ 该记录所有字段断言通过")
                success_count += 1
            else:
                print("  ❌ 该记录存在数据完整性问题")
            print()

        # 6. 清理并返回最终结论
        cursor.close()
        conn.close()

        if success_count == len(results):
            print("=" * 60)
            print("✅ 验证成功！所有入仓任务已完整发布，状态及字段校验全部通过")
            return True
        else:
            print("=" * 60)
            print(f"⚠️ 验证部分通过：仅有 {success_count}/{len(results)} 条记录校验合格")
            return False

    except mysql.connector.Error as e:
        print(f"❌ 数据库连接或执行错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 脚本运行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("用法: python verify_publish_result.py <table_name> <instance_name> <db_name> [wait_time]")
        print()
        print("参数:")
        print("  table_name      - 表名（必需）")
        print("  instance_name   - 实例名（必需）")
        print("  db_name         - 数据库名（必需）")
        print("  wait_time       - 等待时间/秒（可选，默认 30）")
        print()
        print("示例:")
        print("  python verify_publish_result.py batch_test_01 cjjcommon dataops_shitingjie")
        print("  python verify_publish_result.py batch_test_01 cjjcommon dataops_shitingjie 60")
        print()
        print("说明:")
        print("  此脚本用于验证批量入仓任务是否已完整发布到系统")
        print("  根据 TKR_007 规则，验证 4 张关键配置表的数据完整性")
        sys.exit(1)

    table_name = sys.argv[1]
    instance_name = sys.argv[2]
    db_name = sys.argv[3]
    wait_time = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    success = verify_publish_result(table_name, instance_name, db_name, wait_time)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
