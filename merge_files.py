
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col

def main():
    spark = SparkSession.builder \
        .appName("MergeProductFiles") \
        .getOrCreate()

    features_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/garbage/features/date"
    recall_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/recall/garbage_product_merge/date"

    df_features = spark.read.text(features_path) \
        .select(split(col("value"), "\x01").alias("parts")) \
        .select(
            col("parts")[0].alias("product_id"),
            col("parts")[1].alias("shop_id"),
            *[col("parts")[i].alias(f"feature_{i-1}") for i in range(2, 100)]
        )

    df_recall = spark.read.text(recall_path) \
        .select(split(col("value"), "\x01").alias("parts")) \
        .select(
            col("parts")[0].alias("product_id"),
            col("parts")[1].alias("product_title"),
            col("parts")[2].alias("label_1"),
            col("parts")[3].alias("label_2"),
            col("parts")[4].alias("label_3"),
            col("parts")[6].alias("label_4")
        )

    df_merged = df_features.join(df_recall, on="product_id", how="inner")

    df_merged.show()

    output_path = "hdfs://haruna/home/byte_search_ecom/user/taoxinrui/merged_output"
    df_merged.write.mode("overwrite").option("delimiter", "\x01").csv(output_path)

    spark.stop()

if __name__ == "__main__":
    main()

