<div align="center">

# ☕ Running Containers on a Managed Service

### Deploying a containerized Node.js app with **Amazon ECR · Elastic Beanstalk · Aurora Serverless v2 · API Gateway**

![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-App-339933?logo=nodedotjs&logoColor=white)
![MySQL](https://img.shields.io/badge/Aurora-MySQL%20Compatible-4479A1?logo=mysql&logoColor=white)
![Status](https://img.shields.io/badge/Lab-Completed-brightgreen)

</div>

---

## 📖 Overview

In an earlier lab, the **Coffee Suppliers** application was migrated from EC2 instances to Docker containers. In this lab, the same application is deployed using **managed AWS services** to reduce manual maintenance and prepare for future scaling:

| Tier | Service | Why |
|---|---|---|
| 🗄️ Database | **Amazon Aurora Serverless v2** (MySQL compatible) | Relational databases are stateful, so they are a poor fit for dynamic containers. Aurora scales automatically with load and scales down when idle. |
| 🌐 Web | **AWS Elastic Beanstalk** (Docker platform) | Pulls the image from ECR, provisions EC2, load balancer and Auto Scaling automatically. |
| 🔌 API | **Amazon API Gateway** | Exposes the bean inventory (`/beans.json`) to the café website. |
| 📦 Registry | **Amazon ECR** | Stores the `cafe/node-web-app` Docker image. |

## 🏗️ Architecture

```
┌────────────────────┐      ┌─────────────────────┐      ┌──────────────────────────┐      ┌────────────────────────────┐
│  Café website      │ ──▶   Amazon API Gateway    ──▶      Elastic Beanstalk        ──▶   Aurora     Serverless v2   
│  (Amazon S3)       │      │ GET /bean_products  │      │ Docker container on EC2  │      │ (MySQL       compatible)   │
└────────────────────┘      └─────────────────────┘      └────────────┬─────────────┘      └────────────────────────────┘
                                                                      │ pulls image
                                                                      ▼
                                                             ┌──────────────────┐
                                                             │ Amazon ECR       │
                                                             │ cafe/node-web-app│
                                                             └──────────────────┘
```

## 🧰 Services & Tools Used

`Amazon VPC` · `Amazon RDS / Aurora Serverless v2` · `RDS Query Editor` · `Amazon ECR` · `Docker` · `AWS Elastic Beanstalk` · `AWS IAM` · `Amazon API Gateway` · `Amazon S3` · `AWS CLI v2` · `VS Code (code-server) IDE` · `MySQL client`

---

## 🚀 Walkthrough

### 1️⃣ Prepare the environment
Downloaded the lab code, ran `setup.sh` (recreates the S3 website, DynamoDB table, REST API and pushes the Docker image to ECR), and verified the café website.

<img width="1568" height="714" alt="01-cafe-website-s3" src="https://github.com/user-attachments/assets/911882f5-c5e0-4c89-b85c-cfc6840c5e41" />


### 2️⃣ Networking: second subnet + internet route
RDS and a load-balanced Elastic Beanstalk environment need **at least two subnets in different Availability Zones**. I created `extraSubnetForRds` (`10.0.2.0/24`) in a second AZ, enabled auto-assign public IPv4, and associated it with the route table that has a route to the Internet Gateway.

<img width="1568" height="624" alt="02-subnet-route-table" src="https://github.com/user-attachments/assets/a220bf75-f5c9-4d6e-84af-5d29c2dc964c" />


### 3️⃣ Aurora Serverless v2 database
Created the `supplierdb` cluster (Aurora MySQL compatible, Serverless v2, Dev/Test template) inside the **IDE VPC**, attached to the **Lab IDE security group**, with the **RDS Data API** enabled and an initial database named `suppliers`.

<img width="1568" height="629" alt="03-aurora-cluster-available" src="https://github.com/user-attachments/assets/5480475b-cd9d-40e7-8c08-8777daaa099f" />


### 4️⃣ Security group rules
Added two inbound rules to the Lab IDE security group:
- **Custom TCP 8000** from *My IP*, to view the containerized app
- **MYSQL/Aurora 3306** from the security group itself (self-referencing), so the app can talk to the database

<img width="1568" height="579" alt="04-security-group-inbound-rules" src="https://github.com/user-attachments/assets/a52dba37-c459-4325-93a4-01af7dbf22db" />

### 5️⃣ Test the container against Aurora
Started the container with `APP_DB_HOST` pointing to the Aurora cluster endpoint. The home page loaded, but **List of suppliers** returned an error. **This is expected**: the `COFFEE` database, `nodeapp` user and `suppliers` table did not exist yet.

```bash
docker run -d --name node-web-app-1 -p 8000:3000 \
  -e APP_DB_HOST="<aurora-cluster-endpoint>" cafe/node-web-app
```

<img width="1554" height="784" alt="05-app-expected-db-error" src="https://github.com/user-attachments/assets/978905df-cb6b-4011-801c-68e5649305b1" />


### 6️⃣ Create DB objects and load data
Used the **RDS Query Editor** to create the `nodeapp` user, the `COFFEE` database and the `suppliers` table, then loaded the supplier SQL dump with the MySQL client (`source coffee_db_dump.sql`). The app now lists all **8 suppliers** (and the `beans` table has **14 records**).

<img width="1568" height="714" alt="06-suppliers-loaded-from-aurora" src="https://github.com/user-attachments/assets/5ec67bad-ffa3-49b6-b71b-f2b3750b7f63" />


### 7️⃣ IAM review for Elastic Beanstalk
Reviewed `aws-elasticbeanstalk-ec2-instance-policy` (ECR auth token, image pull, Beanstalk `Put*`) and confirmed it is attached to `aws-elasticbeanstalk-ec2-role`, whose trust policy allows `ec2.amazonaws.com`.

<img width="1568" height="622" alt="07-iam-policy-summary" src="https://github.com/user-attachments/assets/0df4d861-e41d-4b4b-84c8-130c2d7d8e7b" />


### 8️⃣ Elastic Beanstalk environment
Created the application and environment from the CLI with an `options.txt` file (instance profile, security group, VPC, both subnets, `APP_DB_HOST`).

```bash
aws elasticbeanstalk create-application --application-name MyNodeApp
aws elasticbeanstalk create-environment \
  --application-name MyNodeApp --environment-name MyEnv \
  --solution-stack-name "64bit Amazon Linux 2023 v4.13.9 running Docker" \
  --region us-east-1 --option-settings file://options.txt
```

<img width="1568" height="626" alt="08-beanstalk-env-launched" src="https://github.com/user-attachments/assets/81a15444-e6f8-4858-89e1-a7f576566fed" />


The default sample application confirmed the platform, load balancer and networking were healthy:

<img width="1568" height="720" alt="09-beanstalk-sample-app" src="https://github.com/user-attachments/assets/d7763d09-abd8-4846-b570-c1661f61cb8e" />


### 9️⃣ Deploy the coffee suppliers container
Created `Dockerrun.aws.json` pointing at the ECR repository (container port `3000`), then used **Upload and deploy** with the version label `MyNodeApp-version-1a`.

<img width="728" height="622" alt="10-upload-and-deploy-dialog" src="https://github.com/user-attachments/assets/906d46b4-ba87-49f8-82aa-c993ab4fec50" />


<img width="1568" height="701" alt="11-beanstalk-deploy-success" src="https://github.com/user-attachments/assets/2ee620d2-0a09-4157-b6d3-4eba37d84225" />


The suppliers page now runs from the Beanstalk URL and reads from Aurora:

<img width="1551" height="784" alt="12-suppliers-on-beanstalk-url" src="https://github.com/user-attachments/assets/aa55239d-c049-4b56-a538-ed52010ea7e0" />


### 🔟 API Gateway proxy → café website
Before the change, the café website's **Buy Coffee** section showed *"Live coffee supply information coming very soon!"*

<img width="1568" height="533" alt="13-buy-coffee-before" src="https://github.com/user-attachments/assets/5c2e2c15-1903-40e8-9074-bde4ff818df7" />


Created the `/bean_products` resource (with CORS) and a `GET` method using an **HTTP proxy integration** to `http://<beanstalk-url>/beans.json`, tested it (status `200`), then deployed to the `prod` stage.

<img width="1568" height="676" alt="14-api-gateway-resources" src="https://github.com/user-attachments/assets/f431b3f5-027a-4b8a-8131-da565b0aad81" />


<img width="735" height="425" alt="15-api-gateway-deploy-dialog" src="https://github.com/user-attachments/assets/83b2e366-3826-4f1e-9826-79c6ebac36e4" />



### ✅ Final result
The Buy Coffee section now shows the live bean inventory (type, price, stock, description) served through API Gateway → Elastic Beanstalk → Aurora Serverless.

<img width="1568" height="717" alt="17-buy-coffee-after-final" src="https://github.com/user-attachments/assets/e2633b54-96a8-4359-b50f-2cf8718cdfa3" />


---

## 🐞 Bugs & Issues I Fixed During the Lab

| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | Second subnet would have been in the wrong AZ | The *Create subnet* page defaults to `us-east-1a`, the same AZ as the IDE subnet. RDS and load-balanced Beanstalk need different AZs. | Selected a different AZ (`us-east-1b`) for `extraSubnetForRds`. |
| 2 | New subnet had no internet access | It was associated with the **Main** route table, which only had the `10.0.0.0/16 → local` route. | Edited the route table association to the other route table containing `0.0.0.0/0 → igw-…`. |
| 3 | RDS *Create database* page had wrong defaults | VPC was **Default VPC**, security group was `default`, cluster name was `database-1`, engine version `3.07.0` from the guide was not offered. | Switched to **IDE VPC**, replaced the SG with **Lab IDE SG**, renamed to `supplierdb`, and used the available version (Aurora MySQL 3.10.3). |
| 4 | ECR value copied with an image tag | Copied the **Image URI** (`…/cafe/node-web-app:latest`) instead of the **Repository URI**. | Removed `:latest` for the Repository URI used in `Dockerrun.aws.json`. |
| 5 | Port 3306 rule incomplete | Third inbound rule had type *Custom TCP* with an empty source. | Changed it to **MYSQL/Aurora** and selected the Lab IDE SG as the source (self-reference). |
| 6 | `ERROR 1045 Access denied for user 'admin'` | Password typed incorrectly (nothing shows while typing in `mysql -p`). | Re-entered the password carefully; the connection succeeded. |
| 7 | Copied connection command would fail | The console *Code snippet* used `--ssl-mode=VERIFY_IDENTITY --ssl-ca=./global-bundle.pem`, but that certificate file isn't on the IDE. | Used the simple command `mysql -h <endpoint> -P 3306 -u admin -p`. |
| 8 | Amazon Linux 2 Docker stack not available | `list-available-solution-stacks` only returned **Amazon Linux 2023 v4.13.9 running Docker**. | Used the AL2023 stack name in `create-environment`; deployment worked with the same `Dockerrun.aws.json`. |
| 9 | `cat: options.txt: No such file or directory` | The file had not been created in the `bean` folder. | Created it from the terminal with a heredoc (`cat > options.txt << 'EOF'`) and verified with `cat`. |
| 10 | `Dockerrun.aws.json` not visible in the upload dialog | The file picker filter only shows `*.zip; *.war; *.jar`. | Typed the file name directly in the *File name* box. |
| 11 | Possible *version label already exists* error | The sample app already used `MyNodeApp-version-1`. | Appended `a` → `MyNodeApp-version-1a`. |
| 12 | Terminal stuck on `:` after AWS CLI output | Output opened in the `less` pager. | Pressed `q` to exit the pager. |
| 13 | Buy Coffee still showed "coming soon" after deploying the API | The browser cached the old page. | Hard refresh (**Ctrl+Shift+R**); the bean cards then loaded. |
| 14 | Red errors: `acm:ListCertificates` / WAF not authorized | Lab sandbox role restrictions. | Safely ignored; they don't affect the task. |
| 15 | `GH007: push would publish a private email address` | GitHub's *Keep my email private* setting blocked the push. | Switched git to my GitHub `noreply` email, ran `git commit --amend --reset-author --no-edit`, and pushed again. |

<details>
<summary><b>Cached page screenshot (bug #13)</b></summary>

<img width="1568" height="716" alt="16-buy-coffee-cached-page" src="https://github.com/user-attachments/assets/b24f3f90-c4cc-49f7-b581-5c79ce25b480" />


</details>

---

## 📚 What I Learned

- Why **stateful relational databases** belong on a managed service (Aurora Serverless v2) rather than in containers
- How to design VPC subnets and route tables for **RDS and Elastic Beanstalk** (multi-AZ, internet gateway route)
- Using **security groups with self-referencing rules** for app-to-database traffic
- Running SQL via the **RDS Query Editor** and the MySQL client, including loading SQL dumps
- Deploying a **single-container Docker environment** to Elastic Beanstalk with `Dockerrun.aws.json` and an IAM instance profile for ECR access
- Fronting a backend with **API Gateway HTTP proxy integration** and CORS
- Debugging real-world cloud issues (AZ selection, routing, DB auth, caching, Git email privacy)

## 📁 Repository Structure

```
.
├── bean/
│   ├── options.txt              # Elastic Beanstalk option settings
│   └── Dockerrun.aws.json       # Single-container Docker deployment config
├── resources/
│   ├── coffee_db_dump.sql       # Supplier + beans data
│   ├── codebase_partner/        # Node.js coffee suppliers app
│   └── website/                 # Café static website
├── screenshots/                 # Lab evidence
└── README.md
```



<div align="center">

Built as part of an AWS Cloud Application Development lab · ☁️ + 🐳 + ☕

</div>
