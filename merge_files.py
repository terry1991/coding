
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, when, concat_ws

def main():
    spark = SparkSession.builder \
        .appName("MergeProductFiles") \
        .getOrCreate()

    features_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/garbage/features/20260601/part-01999-1eb7b3b0-64b5-46f7-aa8d-1cfc1d1c0c8a-c000"
    recall_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/recall/garbage_product_merge/20260527/part-01999-351f2f7c-94ee-4eeb-a40a-41b07cde45b3-c000"

    df_features = spark.read.text(features_path) \
        .select(split(col("value"), "\x01").alias("parts")) \
        .select(
            col("parts")[0].alias("product_id"),
            col("parts")[1].alias("shop_id"),
            *[col("parts")[i].alias(f"feature_{i-1}") for i in range(2, 85)]
        )

    df_recall = spark.read.text(recall_path) \
        .select(split(col("value"), "\x01").alias("parts")) \
        .select(
            col("parts")[0].alias("product_id"),
            col("parts")[1].alias("product_title"),
            col("parts")[2].alias("label_1"),
            col("parts")[3].alias("label_2"),
            col("parts")[4].alias("label_3"),
            col("parts")[6].alias("label_4"),
            col("parts")[7].alias("cate_id"),
            col("parts")[8].alias("cate_name")
        )

    df_merged = df_features.join(df_recall, on="product_id", how="inner")

    df_merged = df_merged.withColumn("label_final",
        when(col("label_1") == 0, 0)
        .when(col("label_2") == 0, 1)
        .when(col("label_3") == 0, 2)
        .when(col("label_4") == 0, 3)
        .otherwise(4)
    )

    df_merged.show()

    output_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/merged_output"
    
    all_columns = df_merged.columns
    df_output = df_merged.select(concat_ws("\x01", *all_columns).alias("value"))
    df_output.write.mode("overwrite").text(output_path)

    spark.stop()

if __name__ == "__main__":
    main()

