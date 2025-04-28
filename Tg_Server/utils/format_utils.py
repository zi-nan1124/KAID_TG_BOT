import pandas as pd
import re
from urllib.parse import quote
from Tg_Server.utils.safe_math import safe_float
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def escape_md(text: str) -> str:
    """转义 MarkdownV2 保留字符"""
    return re.sub(r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', str(text))


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



def escape_markdown_v2(text: str) -> str:
    """完整转义 MarkdownV2 保留字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(rf'([{re.escape(escape_chars)}])', r'\\\1', text)

def escape_md_except_links(text: str) -> str:
    """转义 MarkdownV2 文本，但保留 [xxx](url) 结构，且 URL 进行 quote"""
    parts = re.split(r'(\[.*?\]\(.*?\))', text)  # 拆出超链接
    escaped_parts = []
    for part in parts:
        if part.startswith('[') and part.endswith(')'):
            # 处理链接：[text](url)
            match = re.match(r'\[(.*?)\]\((.*?)\)', part)
            if match:
                text_part = match.group(1)
                url_part = match.group(2)
                # 对标题 escape，对 URL quote
                safe_text = escape_markdown_v2(text_part)
                safe_url = quote(url_part, safe=':/?=&')  # 只保留这些符号，其他都编码
                escaped_parts.append(f'[{safe_text}]({safe_url})')
            else:
                escaped_parts.append(escape_markdown_v2(part))  # 兜底
        else:
            escaped_parts.append(escape_markdown_v2(part))
    return ''.join(escaped_parts)


def escape_md_v2(text: str) -> str:
    """
    转义 MarkdownV2 保留字符，不破坏超链接格式。
    """
    # 用不会被转义污染的占位符，比如 @@LINK0@@
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_pattern, text)

    placeholders = []
    new_text = text

    # 用占位符保护超链接
    for i, (label, url) in enumerate(links):
        placeholder = f"@@LINK{i}@@"
        placeholders.append((placeholder, f"[{label}]({url})"))
        new_text = new_text.replace(f"[{label}]({url})", placeholder)

    # 对非链接部分做 MarkdownV2 转义
    escaped_text = re.sub(r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', new_text)

    # 最后还原占位符
    for placeholder, real_link in placeholders:
        escaped_text = escaped_text.replace(placeholder, real_link)

    return escaped_text

def safe_callback_data(text: str) -> str:
    """
    只允许 a-z, A-Z, 0-9, 下划线，其他一律删除
    """
    return re.sub(r'[^a-zA-Z0-9_]', '', text)

def format_alpha_table(df, max_rows) -> list[tuple[str, InlineKeyboardMarkup]]:
    results = []

    for chain, group_df in df.groupby("chain"):
        # 开头 escape
        lines = [f"*🪙 链：{(chain.upper())}*"]

        groups = {
            "🏆 市值10M以上（貔貅or老币复活）": group_df[group_df["mc"] >= 10_000_000],
            "🥈 市值2M-10M": group_df[(group_df["mc"] >= 2_000_000) & (group_df["mc"] < 10_000_000)],
            "🌱 市值2M以下（潜力股）": group_df[group_df["mc"] < 2_000_000],
        }

        for title, sub_df in groups.items():
            if sub_df.empty:
                continue

            lines.append(f"\n*{(title)}*")
            lines.append(f"{'symbol'} | {'24hVolume'} | {'MarketCap'}")

            for _, row in sub_df.head(max_rows).fillna("-").iterrows():
                symbol_raw = str(row["symbol"])
                address_raw = str(row["address"])
                chain_raw = str(row["chain"])

                # 超链接：只 escape 文本，不 escape URL
                link_text = escape_markdown_v2(symbol_raw)
                url = f"https://www.gmgn.ai/{chain_raw}/token/{address_raw}"
                symbol_link = f"[{symbol_raw}]({url})"  # 这里不管 URL，后面 escape_md_except_links统一处理

                v24 = f"${row['v24hUSD'] / 1_000_000:.2f}M"
                mc = f"${row['mc'] / 1_000_000:.2f}M"

                # ⚡先正常拼接一整行（注意用 '|' 不是 '\\|'）
                raw_line = f"{symbol_link} | {v24} | {mc}"

                # 最后整体 escape（保留超链接结构）
                safe_line = escape_md_v2(raw_line)
                #results.append(safe_line)

                # 按钮
                button = InlineKeyboardButton(
                    text="Mute",
                    callback_data=f"mute_{safe_callback_data(address_raw)}_{safe_callback_data(symbol_raw)}"
                )
                markup = InlineKeyboardMarkup([[button]])

                results.append((safe_line, markup))

    return results

def format_alpha_table_html(df, max_rows=20) -> list[tuple[str, InlineKeyboardMarkup]]:
    results = []

    for chain, group_df in df.groupby("chain"):
        chain_name = chain.upper()

        groups = {
            "🏆 市值10M以上（貔貅or老币复活）": group_df[group_df["mc"] >= 10_000_000],
            "🥈 市值2M-10M": group_df[(group_df["mc"] >= 2_000_000) & (group_df["mc"] < 10_000_000)],
            "🌱 市值2M以下（潜力股）": group_df[group_df["mc"] < 2_000_000],
        }

        for title, sub_df in groups.items():
            if sub_df.empty:
                continue

            # 构建一整块文字
            lines = [f"<b>🪙 链：{chain_name}</b>", f"<b>{title}</b>"]
            buttons = []

            for _, row in sub_df.head(max_rows).fillna("-").iterrows():
                symbol_raw = str(row["symbol"])
                address_raw = str(row["address"])
                chain_raw = str(row["chain"])

                # 超链接
                url = f"https://www.gmgn.ai/{chain_raw}/token/{address_raw}"
                symbol_link = f"<a href='{url}'>{symbol_raw}</a>"

                v24 = f"${row['v24hUSD'] / 1_000_000:.2f}M"
                mc = f"${row['mc'] / 1_000_000:.2f}M"

                # 加到正文
                lines.append(f"{symbol_link} | {v24} | {mc}")

                # 为每个币加一个按钮
                button = InlineKeyboardButton(
                    text=f"Mute {symbol_raw}",
                    callback_data=f"mute_{safe_callback_data(address_raw)}_{safe_callback_data(symbol_raw)}"
                )
                buttons.append([button])  # 一行一个按钮

            # 合并大块文本
            full_text = "\n".join(lines)

            # 创建 markup
            markup = InlineKeyboardMarkup(buttons)

            # 添加到结果
            results.append((full_text, markup))

    return results

