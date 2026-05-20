import json

with open("department_rules.json", "r", encoding="utf-8") as f:
    department_rules = json.load(f)

complaint_type = "illegal_parking"

result = department_rules.get(complaint_type, department_rules["etc"])

print("추천 부서:", result["department"])
print("추천 이유:", result["reason"])
print("연락처:", result["contact"])
print("사이트:", result["website"])
print("준비 서류:", result["required_documents"])
print("추가 안내:", result["extra_info"])