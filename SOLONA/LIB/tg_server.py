from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import pandas as pd
import asyncio
from io import StringIO
from concurrent.futures import ThreadPoolExecutor

from TransactionListDecoder import TransactionListDecoder
from Sol_Wallet_Fetcher import SolanaWalletExplorer
from SOLONA.LIB.TopTrader import TopTraderFinder

executor = ThreadPoolExecutor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 Solana 钱包探索者！\n\n"
        "可用命令包括：\n"
        "`/profit 钱包地址` - 查询 7 日盈利\n"
        "`/decode 签名1 签名2 ...` - 解码交易\n"
        "`/findtoptrader token地址` - 查询 Token 的顶级交易者盈利",
        parse_mode="Markdown"
    )

def format_profit_table(result_df: pd.DataFrame, summary: dict, max_rows: int = 10) -> str:
    lines = []
    lines.append("📊 *收益明细（部分）*")
    lines.append("```\nToken                          | 交易数 | 成本(USD)   | 收益(USD)   | 盈利(USD)   ")
    lines.append("-" * 70)

    for _, row in result_df.head(max_rows).iterrows():
        token = row["token"][:28].ljust(28)
        count = f"{int(row['tx_count']):>5}"
        cost = f"{row['cost']:.2f}".rjust(11)
        income = f"{row['realized_income']:.2f}".rjust(11)
        profit = f"{row['profit']:.2f}".rjust(11)
        lines.append(f"{token} | {count} | {cost} | {income} | {profit}")

    lines.append("```")
    lines.append("🧾 *汇总统计*")
    lines.append(f"```\n总交易数:     {int(summary['total_tx_count'])}")
    lines.append(f"总成本:       ${summary['total_cost']:.2f}")
    lines.append(f"总已实现收益: ${summary['total_realized']:.2f}")
    lines.append(f"总未实现收益: ${summary['total_unrealized']:.2f}")
    lines.append(f"总盈利:       ${summary['total_profit']:.2f}")
    lines.append(f"收益率:       {summary['profit_ratio']}\n```")
    return "\n".join(lines)

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("用法：`/profit 钱包地址`", parse_mode="Markdown")
        return

    wallet_address = context.args[0]
    await update.message.reply_text(f"开始分析地址: `{wallet_address}`，请稍等...", parse_mode="Markdown")

    def blocking_task():
        explorer = SolanaWalletExplorer(config.CONFIG["rpc_url"], wallet_address)
        return explorer.calculate_profit_by_7_day()

    try:
        loop = asyncio.get_event_loop()
        result_df, summary = await loop.run_in_executor(executor, blocking_task)

        if summary is None or result_df is None or result_df.empty:
            await update.message.reply_text("分析失败或交易数据为空。")
            return

        formatted = format_profit_table(result_df, summary)
        await update.message.reply_text(formatted, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"分析时出错：{e}")

async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：`/decode tx1 tx2 ...`（支持多个交易签名）", parse_mode="Markdown")
        return

    sig_list = context.args
    await update.message.reply_text(f"收到 {len(sig_list)} 个交易签名，开始解析中...")

    try:
        df_signatures = pd.DataFrame({"signature": sig_list})
        decoder = TransactionListDecoder()
        final_result = decoder.decode(df_signatures)

        if final_result.empty:
            await update.message.reply_text("❌ 没有解析出任何交易数据。")
            return

        preview = final_result.head(5).to_markdown(index=False)
        await update.message.reply_text(f"✅ 解析完成，前 5 条结果：\n```\n{preview}\n```", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"解析出错：{e}")

def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

async def findtoptrader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("用法：`/findtoptrader token_address`", parse_mode="Markdown")
        return

    token_address = context.args[0]
    await update.message.reply_text(f"🔍 正在获取 Token `{token_address}` 的顶级交易者...", parse_mode="Markdown")

    def blocking_task():
        finder = TopTraderFinder(api_key=config.CONFIG["BIRDEYE_APIKEY"])
        wallet_df = finder.get_wallets(token_address=token_address, limit=10)
        if wallet_df.empty:
            return None, None
        summary_df = finder.batch_calculate_profit_summary(wallet_df)
        return wallet_df, summary_df

    try:
        loop = asyncio.get_event_loop()
        wallet_df, summary_df = await loop.run_in_executor(executor, blocking_task)

        if wallet_df is None or summary_df is None or summary_df.empty:
            await update.message.reply_text("❌ 获取失败或没有数据。")
            return

        preview = summary_df.head(10).fillna("-")
        lines = ["📈 *前 10 名交易者盈利简表：*", "```\n钱包地址                        收益(USD)    收益率"]
        lines.append("-" * 50)
        for _, row in preview.iterrows():
            wallet = row["wallet"][:28].ljust(28)
            profit = f"{safe_float(row.get('total_profit')):.2f}".rjust(10)
            ratio = row.get("profit_ratio", "-")
            lines.append(f"{wallet} {profit}    {ratio}")
        lines.append("```")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

        csv_buffer = StringIO()
        summary_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        await update.message.reply_document(document=csv_buffer, filename="top_trader_summary.csv")

    except Exception as e:
        await update.message.reply_text(f"执行出错：{e}")

def main():
    token = config.CONFIG["telegram_token"]
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profit", profit))
    app.add_handler(CommandHandler("decode", decode))
    app.add_handler(CommandHandler("findtoptrader", findtoptrader))

    print("✅ TG Bot 正在运行中...")
    app.run_polling()

if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    main()
