
# SQL问题分析：doc_type为aweme_video时rag_text为空

## 问题原因

根本原因是 **CONCAT函数遇到NULL值时会返回NULL**。

## 详细分析

### 1. 数据流梳理

整个SQL的处理流程：
```
session_rag → ranked_session → session_rag_aggr → session_rag_text → session_rag_all → rag_ranked
```

### 2. 关键问题点

在 `session_rag_all` CTE 中，doc_type为 `aweme_video` 时的 rag_text 生成逻辑：

```sql
when doc_type in (
    'aweme_video', 
    'aweme_image',
    'double_column_ecom_video') then concat('视频标题:',video_title, ',商品:', product_title, ',店铺:', product_shop_name, ',品牌:', brand_name)
```

### 3. 问题根源

**CONCAT函数特性**：如果CONCAT的任何一个参数是NULL，整个结果就会是NULL。

### 4. 为什么会有NULL值？

看 `session_rag_text` CTE：

```sql
LEFT JOIN search_ecom_dm.ecom_goods_docs_full t2
on t1.product_id = cast(t2.product_id as string) and t2.date = max_pt('search_ecom_dm.ecom_goods_docs_full')
```

这里使用了 **LEFT JOIN**，如果：
- product_id 在 t2 表中不存在
- 或者 t2 表中的 product_title/shop_name/brand_name 字段本身就是NULL

那么：
- t2.product_title → NULL
- t2.shop_name (product_shop_name) → NULL  
- t2.brand_name → NULL

### 5. 结果

当执行 `concat('视频标题:',video_title, ',商品:', NULL, ',店铺:', NULL, ',品牌:', NULL)` 时，整个结果就是 **NULL**。

## 解决方案

### 方案1：使用COALESCE处理NULL值

```sql
concat(
    '视频标题:', COALESCE(video_title, ''), 
    ',商品:', COALESCE(product_title, ''), 
    ',店铺:', COALESCE(product_shop_name, ''), 
    ',品牌:', COALESCE(brand_name, '')
)
```

### 方案2：使用CONCAT_WS（自动忽略NULL）

```sql
concat_ws('',
    '视频标题:', video_title, 
    ',商品:', product_title, 
    ',店铺:', product_shop_name, 
    ',品牌:', brand_name
)
```

### 方案3：检查LEFT JOIN是否应该改为INNER JOIN

如果这些字段对业务是必需的，考虑将LEFT JOIN改为INNER JOIN，但这会过滤掉没有匹配的数据。

## 验证方法

可以添加调试查询来确认：

```sql
SELECT 
    doc_type,
    video_title,
    product_title,
    product_shop_name,
    brand_name,
    concat('视频标题:',video_title, ',商品:', product_title, ',店铺:', product_shop_name, ',品牌:', brand_name) as rag_text
FROM session_rag_text
WHERE doc_type = 'aweme_video'
LIMIT 100;
```

这样就能看到哪些字段是NULL了。
