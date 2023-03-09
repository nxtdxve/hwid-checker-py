# **License Management System**

The License Management System is a web application that helps software companies manage their licensing and registration processes. It consists of two parts - the main application and the admin panel.

The main application is used by end-users to enter a valid serial key and register their account. Once registered, they can perform various system-related tasks such as checking for updates, obtaining their system's hardware ID, and more.

The admin panel, on the other hand, is used by software companies to manage their licensing and user accounts. It allows companies to generate license keys, track user registrations, disable or enable user accounts, and view user information.

## **Table of Contents**

- **[Installation](https://github.com/nxtdxve/hwid-checker-py#installation)**
- **[Usage](https://github.com/nxtdxve/hwid-checker-py#usage)**
- **[Contributing](https://github.com/nxtdxve/hwid-checker-py#contributing)**
- **[License](https://github.com/nxtdxve/hwid-checker-py#license)**

## **Installation**

To install the License Management System, follow these steps:

1. Clone the repository to your local machine.
    
    ```
    git clone https://github.com/nxtdxve/hwid-checker-py
    ```
    
2. Install the required dependencies using **`pip`**.
    
    ```
    pip install -r requirements.txt
    ```
    
3. Set up any necessary configuration files and environment variables.

    ```
    DB_URI='mongodb+srv://username:password@cluster-name.mongodb.net/database-name'
    DB_NAME='database-name'
    REPO_OWNER='username'
    REPO_NAME='repo-name'
    VERSION='v1.0.0'
    ```

4. Run the application using **`python`**.
    
    ```
    python main.py
    ```
    

## **Usage**

Upon launching the License Management System, you will be prompted to enter a serial key. If the key is valid and has not been used before, you will be prompted to enter a username. If the username is valid, your account will be registered, and you will be able to use the License Management System.

The License Management System allows you to perform various system-related tasks, such as generating license keys for your software, managing user registrations, and disabling or enabling user accounts as needed.

## **Contributing**

Contributions to My Application are always welcome! If you find any bugs or have any suggestions for improvement, please submit a pull request or open an issue.

## **License**

This project is licensed under the **[MIT License](https://github.com/nxtdxve/hwid-checker-py/blob/master/LICENSE.md)**.

---

Developed by **[David Zettler](https://github.com/nxtdxve)**
