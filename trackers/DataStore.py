
# Imports ====================================================================================
import csv
import json
import pandas as pd
from dataclasses import dataclass

# Helper Functions ====================================================================================
def detect_type(data: any) -> str:
  if isinstance(data, list):
      return "list"
  elif isinstance(data, dict):
      return "dict"
  elif hasattr(data, "__dict__"):
      return "instance"
  else:
      return "other"

# Classes ====================================================================================
@dataclass
class DataStore:
  @staticmethod
  def saveData(fileName: str, obj: any) -> None:
      fileName += ".json"

      if isinstance(obj, list):
          data = [o.__dict__ if hasattr(o, "__dict__") else o for o in obj]
      else:
          data = obj.__dict__ if hasattr(obj, "__dict__") else obj

      with open(fileName, "w") as file:
          json.dump(data, file, indent=4)

      print(f"\033[32mData saved as `{fileName}\033[0m")

  @staticmethod
  def loadData(fileName: str) -> list[dict]:
    fileName += ".json"
    with open(fileName, "r") as file:
      data = json.loads(file.read())
      if (detect_type(data) == "dict"):
          data = [data]

      print(f"\033[32mData loaded from `{fileName}\033[0m")
      return data

  @staticmethod
  def flatten_for_analysis(data: any, file_name="./storage/data.csv") -> None:
      dtype = detect_type(data)

      def convert(obj: any) -> dict:
          if detect_type(obj) == "instance":
              return obj.__dict__
          return obj

      if dtype == "instance":
          data = [convert(data)]
      elif dtype == "dict":
          data = [data]
      elif dtype == "list":
          data = [convert(d) for d in data]
      else:
          raise TypeError(f"Unsupported data type: {dtype}")

      df = pd.json_normalize(data, sep="_")

      list_cols = [col for col in df.columns if any(isinstance(x, list) for x in df[col])]
      for col in list_cols:
          df = df.explode(col)

      df.to_csv(file_name, index=False)

      print(f"\033[32mCSV saved as '{file_name}'\033[0m")