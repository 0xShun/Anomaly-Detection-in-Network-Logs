> NOTE: Every time you read this make sure when you are coding you must follow proper coding techniques, clean code and simple code. 

# Background information
This project is a real-time log anomaly detection web platform designed for administrators to monitor and respond to suspicious activity in network and authentication logs. The system is built on an AWS Free Tier infrastructure with four Ubuntu EC2 instances, where three hosts act as log producers sending continuous event streams to a central Kafka broker, and one host (the main server) consumes these logs, preprocesses them, and runs inference using a LogBERT unsupervised anomaly detection model. The model assigns each log an anomaly score, and any log exceeding a configurable threshold is tagged as anomalous and published to a dedicated Kafka topic for anomalies. The admin-facing Streamlit dashboard provides secure authentication, real-time anomaly feeds, historical log details, interactive visualizations (line, bar, and pie charts), and a system monitoring panel showing the live status of Kafka, Zookeeper, and the consumer process. Administrators can also configure the anomaly score threshold and manage platform settings directly from the web interface, enabling dynamic tuning without redeployment. This integration of big data streaming (Kafka), machine learning (LogBERT), and interactive visualization (Streamlit) creates a robust, scalable, and user-friendly platform for proactive anomaly detection and incident response.

Got it ✅
I’ll turn the **admin web platform features** we listed earlier into a **detailed markdown checklist** with clear, step-by-step instructions so Cursor AI can implement them without ambiguity.
I’ll make sure to structure it in a way that’s explicit about pages, components, and data sources.

---

# FEATURES:

## **1. Authentication & Access Control**

* [ ] **Implement Login Page**

  * Create a login form with fields:

    * **Username** (string, required)
    * **Password** (string, required, masked input)
  * Add a **Login** button that triggers authentication logic.
  * On successful login:

    * Store an authenticated session (e.g., using `st.session_state` in Streamlit).
    * Redirect the user to the Dashboard Overview page.
  * On failed login:

    * Display an error message (“Invalid username or password”).
* [ ] **Restrict Dashboard Access**

  * Only allow logged-in admins to view dashboard pages.
  * Redirect non-authenticated users to the login page.
* [ ] **Logout Functionality**

  * Add a “Logout” button that clears the session state and redirects to login.

---

## **2. Dashboard Overview Page**

* [ ] **Page Layout**

  * Use a **3-column grid** at the top for summary cards.
  * Below the summary cards, include real-time data visualizations and anomaly tables.
* [ ] **Summary Cards** (each card should display live data)

  * **Total Logs Processed** (integer, updates in real-time)
  * **Total Anomalies Detected** (integer, updates in real-time)
  * **Current System Status** (green/red indicator, based on system status checks)
* [ ] **Real-Time Anomaly Feed Table**

  * Columns: `Timestamp`, `Log Message`, `Anomaly Score`
  * Data source: Kafka topic `anomalies`
  * Update automatically without page reload (e.g., using Streamlit’s `st.experimental_rerun` or timed refresh).
* [ ] **Auto-refresh Functionality**

  * Set the page to refresh data every 5 seconds without losing the UI state.

---

## **3. Visualizations**

* [ ] **Line Chart**

  * X-axis: Time (e.g., last 24 hours)
  * Y-axis: Count of anomalies
  * Data source: Kafka `anomalies` topic (aggregated by time window)
* [ ] **Bar Chart**

  * X-axis: Source (IP or hostname)
  * Y-axis: Number of anomalies from that source
  * Data source: parsed log fields from anomalies
* [ ] **Pie Chart**

  * Segments: Anomaly categories/types (if available from preprocessing)
  * Data source: categorized anomalies

---

## **4. Log Details Page**

* [ ] **Search & Filter Logs**

  * Filter by date range (start date, end date).
  * Filter by anomaly score threshold.
  * Filter by hostname or IP address.
* [ ] **Log Table**

  * Columns: `Timestamp`, `Host/IP`, `Log Message`, `Anomaly Score`
  * Support pagination for large datasets.
* [ ] **Data Source**

  * Pull from Kafka `anomalies` topic for anomalies.
  * Optionally pull from `logs` topic for raw logs (if needed).

---

## **5. System Monitoring Page**

* [ ] **System Status Panel**

  * Display status for:

    * Kafka Broker (🟢 Running / 🔴 Stopped)
    * Zookeeper Service (🟢 Running / 🔴 Stopped)
    * Consumer Process (🟢 Running / 🔴 Stopped)
  * Implement backend checks:

    * Kafka status via `KafkaAdminClient` connection test.
    * Zookeeper status via TCP socket connection to port 2181.
    * Consumer process status via process ID check.
* [ ] **Log Ingestion Rate**

  * Display messages per second from Kafka `logs` topic.

---

## **6. Settings Page**

* [ ] **Anomaly Score Threshold Control**

  * Add a slider to adjust threshold (range: 0.0 to 1.0, default: 0.5).
  * Store threshold in a persistent location (file or small DB) so it remains after restart.
* [ ] **Admin Account Management**

  * Ability to update admin username/password (stored securely with hashing).
* [ ] **Kafka Connection Settings**

  * Input fields for Kafka broker address and port.
  * Save settings to config file.

---

## **7. General Requirements**

* [ ] **Consistent Navigation**

  * Add a sidebar or top menu for navigation between:

    * Dashboard Overview
    * Log Details
    * System Monitoring
    * Settings
    * Logout
* [ ] **Responsive Design**

  * Ensure layout works on both desktop and tablet screens.
* [ ] **Error Handling**

  * Display clear error messages if Kafka/Zookeeper is down.
  * Handle empty datasets gracefully.

---

If you want, I can also prepare **exact JSON structures for Kafka messages** so Cursor AI knows the expected data formats for the logs and anomalies.
Do you want me to add that next?
