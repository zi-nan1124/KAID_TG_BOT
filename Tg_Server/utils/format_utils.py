import pandas as pd
from Tg_Server.utils.safe_math import safe_float

def format_profit_table(result_df, summary, max_rows=10) -> str:
    lines = []
    lines.append("*收益明细（部分）*")
    lines.append("```")
    lines.append(
        f"{'Token':<30} {'交易数':>5} {'成本(USD)':>12} {'已实现收益(USD)':>16} {'未实现收益(USD)':>16} {'盈利(USD)':>12}"
    )
    lines.append("-" * 95)

    for _, row in result_df.head(max_rows).iterrows():
        token = row["token"][:30]
        lines.append(
            f"{token:<30} {int(row['tx_count']):>5} {row['cost']:>12.2f} {row['realized_income']:>16.2f} {row['unrealized_income']:>16.2f} {row['profit']:>12.2f}"
        )

    lines.append("```")
    lines.append("*汇总统计*")
    lines.append("```")
    lines.append(f"总交易数:     {int(summary['total_tx_count'])}")
    lines.append(f"总成本:       ${summary['total_cost']:.2f}")
    lines.append(f"总已实现收益: ${summary['total_realized']:.2f}")
    lines.append(f"总未实现收益: ${summary['total_unrealized']:.2f}")
    lines.append(f"总盈利:       ${summary['total_profit']:.2f}")
    lines.append(f"收益率:       {summary['profit_ratio']}")
    lines.append("```")

    return "\n".join(lines)


def format_toptrader_table(df: pd.DataFrame, max_rows: int = 10) -> str:
    lines = ["*前 10 名交易者盈利简表：*", "```"]
    lines.append("钱包地址                        收益(USD)    收益率")
    lines.append("-" * 50)
    for _, row in df.head(max_rows).fillna("-").iterrows():
        wallet = row["wallet"][:28].ljust(28)
        profit = f"{safe_float(row.get('total_profit')):.2f}".rjust(10)
        ratio = row.get("profit_ratio", "-")
        lines.append(f"{wallet} {profit}    {ratio}")
    lines.append("```")
    return "\n".join(lines)

import re

def escape_md(text: str) -> str:
    """转义 MarkdownV2 保留字符"""
    return re.sub(r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', str(text))


def format_alpha_table(df, max_rows) -> str:
    lines = ["*新地址更新（按链划分，每链前 %d 项）*:" % max_rows]

    for chain, group_df in df.groupby("chain"):
        lines.append(f"\n*链：{escape_md(chain.upper())}*")
        lines.append("symbol \\| 24hVolume \\| MarketCap")

        for _, row in group_df.head(max_rows).fillna("-").iterrows():
            symbol_raw = str(row["symbol"])
            address_raw = str(row["address"])
            chain_raw = str(row["chain"])[:3]

            # 构造超链接
            link_text = escape_md(symbol_raw)
            url = escape_md(f"https://www.gmgn.ai/{chain_raw}/token/{address_raw}")
            symbol_link = f"[{link_text}]({url})"

            v24 = f"{row['v24hUSD'] / 1_000_000:.2f}"
            mc = f"{row['mc'] / 1_000_000:.2f}"

            # 整行字符串，除了超链接部分都 escape
            volume_text = escape_md(f"${v24}M")
            mc_text = escape_md(f"${mc}M")

            # 拼接
            line = f"{symbol_link} \\| {volume_text} \\| {mc_text}"
            lines.append(line)

    return "\n".join(lines)





