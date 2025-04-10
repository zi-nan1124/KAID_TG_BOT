# MEXC_SMART_WALLET_20250401

## 第一阶段：数据基础阶段（2 day）

### 工作内容概述：

**将 Solana 链上原始交易数据结构化解析为清晰的可读行为，如“谁 用 几个 SOL 交换了 几个 Token”。**

### 工作量：

### 1. 常见protocol（raydium orca Lifinity ）（完成）：

- **raydium v3：**

- 2a36tnsNo1hVi6suPSq1g7ophgQbMykfqTLB4n93tyvprNMBpPYTikvixtYzfGt4EFk1235bGTbRNdejKzPmHrq9

- **raydium v4 RVKd61ztZW9C9vjaHh7bQzToy9ktsLk2YVEcENKB76o：**

- qp3qiQNwhD6rnFVoZhakcD6Cu4Y7gLDQNDHA72yZiNAGKK5NrvxxRJ8Y4jaaqdArm7wBVFmGbUDMkqtkC3peiA9

### 2. Jupiter：HELIU API SUCCESSFULLY（完成）

- **jupiterV6 JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4:**
- GeuLLrzN1bZm9LwxFgmWZ5SBkv13eVk15LHBkLSq4AGuHcW5QRTSgtQueMXHu2YQ8BPfws7srQKZtsvEWZEU9KA
- **pump.fun+jupiter**：
- 315nC8kiG4grNsUUnK3sUrQ7dhbnppBoViKXBbzAFB2pEjZekL77ArmsCXaN5EwLx6qxDx4cvprLntbHvfTphtLP        

### 3. pumpfun: 

**pumpfun.amm pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA（完成）:**

- **sell:**
- 4gUFp7tUMqPn1FWFUzUm4pLByYiZTNu28gUJkGNsVrKYPRkeQnqwBZVVkeUd2rqQ11bHT5bJwnTK7h5RiYW1X5wp
- 5GLdUXrwiCJzvn8D98PEJmRhyh9Z62vc86MpgmtCR8twjkgni8yPPe1jgsPkpJ3gUNKHbYRrZLh5vtY4tATVnr2X
- **buy:**
- MNuqWoyfPhZH55bna1KXCygN6WGDXa72bRU9HmRJABd48iEAuLBxgPWkLddJ5krhXsmsejDpXy5oM9c4iyQLj9d
- 2npZvgP5QqfTAsxc4Z26Y7tYGSgQZBtNovEgb3zZFSFPgv2umPN8YRve7d9c74fghEvY3BdK1N9x8qJkXaBe3ut5

**pump.fun 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P:**

- **sell:**
- 2y9ngxbiFwH3DV398enfTHJSf9vKsrBhoNSYQq86ay8VfjqWqmrxr746R5jFknZQFvjmKG8tHcpyyLoY2w2AVJK5
- **buy:**
- 21YuCoLJhKM3N6MFzXnaSnmsMUZFa9by7CUVXutbNtFHr9U8nxpsYpxLTDCP3K5N48p49Y3UaFxzxxM2KEv2bZMy

#### test wallet:

DW1DdpQ9JGY4up2yRSg8gKeH9ZwG9xXvywgA6GfWo99a

### 工作意义：

**作为后续所有链上分析、策略执行与数据追踪的底层基础设施模块，是全链数据能力的核心支撑。**

### 工作难点：

**Solana 链上协议又乱又多，基础 RPC 接口能力不完整，需在高可扩展性和高性能的前提下，构建可持续演进的解析组件。**

**内含两个核心挑战：**
**高性能**： 模块需支持后续地**巨量**调用，**性能瓶颈将限制整个系统**；
**可拓展性**： 必须留好适配未来 DEX 结构变化与新协议支持的接口。



## 第二阶段  GMGN复刻 （2-3 day）

### 算法：

**混合盈亏算法（SOL/USDC双资产追踪 + 当前快照）**

- **总成本 = 支出 SOL*SOL现价 + 支出 USDC/T**
- **已实现收入 = 获得 SOL*SOL现价 + 获得 USDC/T**
- **未实现收入 = 当前 token 持仓价值 * token现价**
- **净盈利 = 实现 + 未实现 - 成本**

### **难点：**

- pumpfun内盘代币的现价 历史成交价

### 意义：

* 自主构建 GMGN 系统可支持批量查询数百上千个钱包地址的盈亏数据，极大提升数据获取效率，避免手动逐个复制粘贴所带来的低效与误差。
* 由于现有 GMGN 系统未对外开放 API，若不搭建自主版本，将难以进行后续的聪明资金识别、标签化与策略开发等深度链上行为分析工作。

------

## 第三阶段：GMGN升级（？day）

### 升级思路1 ：对于transfer事件的处理

**高估已实现利润**（转入的 token 卖了当盈利）

**高估未实现利润**（转入的 token 被算进了你的仓位）

**低估未实现利润**（买入的token被转走）

### 1. **记录 token 的来路**

为每个 token 引入一个“**持仓来源追踪机制**”（来源标签）：

| token | 数量 | 来源     |
| ----- | ---- | -------- |
| JUP   | 500  | swap购买 |
| JUP   | 300  | 他人转账 |

你可以：

- **只将 swap 或你主钱包转入 的 token 算入成本逻辑**
- 其他来源作为“无成本持仓”，单独处理盈利

### 2. **处理主动转出 token 的情况**

这种情况代表用户把 token 提走了：

- 不应算作亏损
- 可以打标签：**"未实现利润转移"**，并提示已不在当前钱包中

**可选：允许用户追踪多个钱包的“联合收益”**



### 升级思路2： 价格计算 接入计算曲线

![image-20250401103755001](C:\Users\61427\AppData\Roaming\Typora\typora-user-images\image-20250401103755001.png)



## 第四阶段：聪明钱追踪策略

### top_trader追踪策略（1-2day）

1. **输入一个交易池（LP）地址**
    → 获取该池子所交易的 **非稳定币 token 的 mint address**
2. **获取该 token 所有 holder（通过 Token Program）**
   - 使用 `getTokenLargestAccounts` 或全量 holder 列表
   - 过滤掉 SOL、USDC、USDT 等稳定币/主币
3. **过滤条件：**
   - 只保留余额大于 `X` 的地址（如 ≥1000 sol）
4. **遍历每个钱包：**
   - 抽取该钱包与该 token 相关的所有交易（包括 swap、transfer）
   - 用之前你定义的**混合盈利算法**计算：
     - 成本（买入支出）
     - 已实现利润（卖出收益）
     - 未实现利润（当前持仓价值）
     - 总盈利
5. **按盈利排序，取前 10 名作为聪明钱**
6. **输出分析结果**：地址、盈利、ROI、持仓、交易次数等

 

### KOL追踪（1-2day）

**输入：**

- `KOL_addr`：KOL 的钱包地址
- `[T1, T2, ..., Tn]`：目标 token mint 地址列表

**KOL 买入时间提取（每个 token）**

- 遍历该 KOL 的交易历史
- 找到第一次获得每个 token 的时间 `T_buy_time[KOL][Ti]`

**早期买家识别（每个 token）**

- 针对每个 token Ti，找出所有**在该时间点前有过买入行为**的钱包地址
- 得到地址集合 `S[Ti]`

**集合交集计算**

- 取多个集合的交集：

  SmartSet=S[T1]∩S[T2]∩⋯∩S[Tn]\text{SmartSet} = S[T1] \cap S[T2] \cap \dots \cap S[Tn]SmartSet=S[T1]∩S[T2]∩⋯∩S[Tn]

- 表示这些地址在每个 token 上都**先于 KOL**买入

**输出结果（附带扩展信息）**

- 地址、提前买入次数、是否持仓、是否盈利等





根据pump行为去追踪聪明钱（）

输入 token 时间 





## 第五阶段 监控聪明钱包

监控

## 第六阶段 交易

调用dex api



扒庄



