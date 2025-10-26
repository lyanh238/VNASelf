# VNASelf Documentation

Welcome to the VNASelf documentation! This directory contains comprehensive guides and references for the VNASelf multi-agent system with modern React frontend.

## Documentation Index

### Getting Started
- **[README](../README.md)** - Main project overview and quick start guide
- **[Setup Guide](SETUP.md)** - Detailed installation and configuration instructions
- **[Usage Guide](USAGE.md)** - How to use the application effectively

### Technical Documentation
- **[Architecture Guide](ARCHITECTURE.md)** - System architecture and design decisions
- **[API Documentation](API.md)** - Complete API reference and integration guide
- **[Finance Agent Guide](FINANCE_AGENT.md)** - Finance management features and usage

### Troubleshooting
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## Quick Start

1. **Installation**: Follow the [Setup Guide](SETUP.md) to install and configure VNASelf
2. **Basic Usage**: Read the [Usage Guide](USAGE.md) to learn how to interact with the system
3. **Finance Features**: Check the [Finance Agent Guide](FINANCE_AGENT.md) for expense management
4. **Technical Details**: Review the [Architecture Guide](ARCHITECTURE.md) for system design

## System Overview

VNASelf is a multi-agent personal assistant with a modern React frontend that helps you manage:

- **Personal Finance**: Track expenses, view spending history, and analyze your financial habits
- **Calendar Management**: Schedule events, check availability, and manage your time
- **Intelligent Routing**: Automatically routes your requests to the appropriate specialized agent
- **Chat History**: Persistent conversation history stored in NeonDB
- **Modern UI**: Beautiful React interface with dark/light theme support

## Key Features

### Modern React Frontend
- Beautiful, responsive user interface
- Dark and light theme support
- Real-time chat interface
- Conversation history sidebar
- Mobile-friendly design
- Smooth animations and transitions

### Finance Management
- Add and track expenses with categories (Food, Transportation, Miscellaneous)
- View spending history and calculate totals
- Filter expenses by date ranges
- Full Vietnamese language support

### Calendar Integration
- Create, update, and delete calendar events
- Check for scheduling conflicts
- View upcoming events and availability
- Intelligent conflict resolution

### Multi-Agent Architecture
- Supervisor Agent for intelligent routing
- Finance Agent for expense management
- Calendar Agent for Google Calendar integration
- Clear agent identification in responses
- Persistent conversation logs in NeonDB

### Backend API
- FastAPI-based REST API
- WebSocket support for real-time communication
- Chat history management
- Thread-based conversation organization

## Getting Help

If you encounter any issues:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for common solutions
2. Review the [API Documentation](API.md) for technical details
3. Read the [Usage Guide](USAGE.md) for proper usage patterns
4. Create an issue in the repository for specific problems

## Version Information

- **VNASelf Version**: 1.0.0
- **Python Requirements**: 3.11+
- **Dependencies**: See requirements.txt in the main directory

## Contributing

We welcome contributions! Please see the main README.md for contribution guidelines.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Happy using VNASelf!**