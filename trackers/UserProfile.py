import DataStore
from datetime import datetime
from dataclasses import dataclass

@dataclass
class UserProfile:
  name: str
  age: int
  weight: float
  gender: str

  dailyWaterNeeds: float
  dailyCalorieNeeds: float

  waterDrunk: float = 0
  caloriesConsumed: float = 0

  def dailyWaterNeeds(self) -> float:
    return self.dailyWaterNeeds - self.waterDrunk
  
  def dailyCalorieNeeds(self) -> float:
    return self.dailyCalorieNeeds - self.caloriesConsumed
  
  def saveUser(self):
    DataStore.DataStore.saveData("./storage/user", self)

  @staticmethod
  def loadUser(cls):
    return cls(**DataStore.DataStore.loadData("./storage/user"))
  
def test():
  user = UserProfile("Youssef Beshnack", 20, 73.2, "Male", 3000, 2000)
  user.saveUser()

test()