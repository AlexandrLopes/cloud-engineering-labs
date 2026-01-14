# DynamoDB Security Logger

A Python automation script that interacts with **AWS DynamoDB (NoSQL)**. It acts as a centralized log handler for security events.

### Features
* **Infrastructure on Demand:** Uses `boto3` to check if the database table exists. If not, it creates it programmatically.
* **Data Ingestion:** Inserts structured JSON logs (Security Alerts) into the database.
* **Error Handling:** Manages AWS exceptions like `ResourceInUseException`.

### Tech Stack
* Python 3
* Boto3 (AWS SDK)
* AWS DynamoDB

### Usage
```bash
python main.py