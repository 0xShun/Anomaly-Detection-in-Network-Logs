#!/bin/bash
###############################################################################
# Kafka Helper Script
# Manages Kafka and Zookeeper services for LogBERT demo
#
# Usage:
#   ./kafka_helper.sh start    - Start Zookeeper and Kafka
#   ./kafka_helper.sh stop     - Stop Kafka and Zookeeper
#   ./kafka_helper.sh status   - Check if services are running
#   ./kafka_helper.sh create   - Create log_topic
#
# Author: LogBERT Platform
###############################################################################

set -e

# Configuration
KAFKA_HOME="$HOME/kafka_2.13-3.6.1"
KAFKA_TOPIC="log_topic"
KAFKA_PORT=9092
ZOOKEEPER_PORT=2181

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Kafka is installed
check_kafka_installation() {
    if [ ! -d "$KAFKA_HOME" ]; then
        print_error "Kafka not found at $KAFKA_HOME"
        echo "Please install Kafka or update KAFKA_HOME in this script"
        exit 1
    fi
    print_success "Kafka found at $KAFKA_HOME"
}

# Check if Zookeeper is running
check_zookeeper_running() {
    if lsof -Pi :$ZOOKEEPER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if Kafka is running
check_kafka_running() {
    if lsof -Pi :$KAFKA_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start Zookeeper
start_zookeeper() {
    print_info "Starting Zookeeper..."
    
    if check_zookeeper_running; then
        print_warning "Zookeeper is already running on port $ZOOKEEPER_PORT"
        return 0
    fi
    
    # Start Zookeeper in background
    nohup "$KAFKA_HOME/bin/zookeeper-server-start.sh" \
        "$KAFKA_HOME/config/zookeeper.properties" \
        > /tmp/zookeeper.log 2>&1 &
    
    # Wait for Zookeeper to start
    sleep 3
    
    if check_zookeeper_running; then
        print_success "Zookeeper started on port $ZOOKEEPER_PORT"
        return 0
    else
        print_error "Failed to start Zookeeper"
        echo "Check logs: tail -f /tmp/zookeeper.log"
        return 1
    fi
}

# Start Kafka
start_kafka() {
    print_info "Starting Kafka..."
    
    if check_kafka_running; then
        print_warning "Kafka is already running on port $KAFKA_PORT"
        return 0
    fi
    
    # Ensure Zookeeper is running
    if ! check_zookeeper_running; then
        print_error "Zookeeper must be running before starting Kafka"
        return 1
    fi
    
    # Start Kafka in background
    nohup "$KAFKA_HOME/bin/kafka-server-start.sh" \
        "$KAFKA_HOME/config/server.properties" \
        > /tmp/kafka.log 2>&1 &
    
    # Wait for Kafka to start
    sleep 5
    
    if check_kafka_running; then
        print_success "Kafka started on port $KAFKA_PORT"
        return 0
    else
        print_error "Failed to start Kafka"
        echo "Check logs: tail -f /tmp/kafka.log"
        return 1
    fi
}

# Stop Kafka
stop_kafka() {
    print_info "Stopping Kafka..."
    
    if ! check_kafka_running; then
        print_warning "Kafka is not running"
    else
        "$KAFKA_HOME/bin/kafka-server-stop.sh"
        sleep 3
        print_success "Kafka stopped"
    fi
}

# Stop Zookeeper
stop_zookeeper() {
    print_info "Stopping Zookeeper..."
    
    if ! check_zookeeper_running; then
        print_warning "Zookeeper is not running"
    else
        "$KAFKA_HOME/bin/zookeeper-server-stop.sh"
        sleep 2
        print_success "Zookeeper stopped"
    fi
}

# Create Kafka topic
create_topic() {
    print_info "Creating Kafka topic: $KAFKA_TOPIC"
    
    if ! check_kafka_running; then
        print_error "Kafka must be running to create topics"
        return 1
    fi
    
    # Check if topic already exists
    if "$KAFKA_HOME/bin/kafka-topics.sh" \
        --bootstrap-server localhost:$KAFKA_PORT \
        --list 2>/dev/null | grep -q "^${KAFKA_TOPIC}$"; then
        print_warning "Topic '$KAFKA_TOPIC' already exists"
        
        # Show topic details
        echo ""
        print_info "Topic details:"
        "$KAFKA_HOME/bin/kafka-topics.sh" \
            --bootstrap-server localhost:$KAFKA_PORT \
            --describe \
            --topic "$KAFKA_TOPIC"
        return 0
    fi
    
    # Create topic
    "$KAFKA_HOME/bin/kafka-topics.sh" \
        --bootstrap-server localhost:$KAFKA_PORT \
        --create \
        --topic "$KAFKA_TOPIC" \
        --partitions 3 \
        --replication-factor 1
    
    if [ $? -eq 0 ]; then
        print_success "Topic '$KAFKA_TOPIC' created successfully"
        echo ""
        print_info "Topic configuration:"
        echo "  - Partitions: 3"
        echo "  - Replication Factor: 1"
        echo "  - Retention: Default (7 days)"
    else
        print_error "Failed to create topic '$KAFKA_TOPIC'"
        return 1
    fi
}

# Show status
show_status() {
    print_header "Service Status"
    
    echo -n "Zookeeper (port $ZOOKEEPER_PORT): "
    if check_zookeeper_running; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    echo -n "Kafka (port $KAFKA_PORT): "
    if check_kafka_running; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    # Show topics if Kafka is running
    if check_kafka_running; then
        echo ""
        print_info "Kafka Topics:"
        "$KAFKA_HOME/bin/kafka-topics.sh" \
            --bootstrap-server localhost:$KAFKA_PORT \
            --list 2>/dev/null || echo "  (none)"
    fi
    
    echo ""
    print_info "Log files:"
    echo "  Zookeeper: /tmp/zookeeper.log"
    echo "  Kafka: /tmp/kafka.log"
}

# Main command handler
case "${1:-}" in
    start)
        print_header "Starting Kafka Services"
        check_kafka_installation
        start_zookeeper
        start_kafka
        echo ""
        print_success "All services started!"
        echo ""
        print_info "Next steps:"
        echo "  1. Create topic: ./kafka_helper.sh create"
        echo "  2. Start producer: python3 kafka_log_producer.py <log_file>"
        echo "  3. Start consumer: python3 kafka_consumer_api_sender.py --api-url https://logbert.pythonanywhere.com"
        ;;
    
    stop)
        print_header "Stopping Kafka Services"
        stop_kafka
        stop_zookeeper
        print_success "All services stopped"
        ;;
    
    status)
        show_status
        ;;
    
    create)
        print_header "Creating Kafka Topic"
        create_topic
        ;;
    
    restart)
        print_header "Restarting Kafka Services"
        stop_kafka
        stop_zookeeper
        sleep 2
        start_zookeeper
        start_kafka
        print_success "Services restarted"
        ;;
    
    *)
        echo "Kafka Helper Script for LogBERT Platform"
        echo ""
        echo "Usage: $0 {start|stop|status|create|restart}"
        echo ""
        echo "Commands:"
        echo "  start    - Start Zookeeper and Kafka"
        echo "  stop     - Stop Kafka and Zookeeper"
        echo "  status   - Check service status"
        echo "  create   - Create log_topic"
        echo "  restart  - Restart all services"
        echo ""
        echo "Examples:"
        echo "  $0 start        # Start services"
        echo "  $0 create       # Create topic"
        echo "  $0 status       # Check status"
        exit 1
        ;;
esac
