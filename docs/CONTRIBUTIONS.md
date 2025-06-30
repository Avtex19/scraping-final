# Project Contributions

## Overview

This document outlines the contributions made by each team member to the Advanced Web Scraping Framework project. The development was a collaborative effort between us, with an equal 50-50 contribution split demonstrating balanced teamwork and shared responsibility.

## Contributors

| Contributor | GitHub Username | Email |
|-------------|----------------|----------------|
| **Giorgi Sakhelashvili** | SakhelaTheInvincible | sakhelashvili.giorgi@kiu.edu.ge
| **Avtandil Beradze** | Avtex19 | beradze.avtandili@kiu.edu.ge

---

## 👨‍💻 Giorgi's Contributions

### **Primary Areas of Responsibility**

#### Advanced Scraping Framework
- **`scrapy_crawler`**: Complete Scrapy implementation
  - Amazon spider development with anti-bot protection
  - Custom middleware for rate limiting and user-agent rotation
  - Advanced CAPTCHA detection and handling
  - Retry mechanisms with exponential backoff
  - Database integration with job tracking

#### Configuration Management
- **`config`**: Complete configuration system implementation
  - YAML configuration schema design
  - Hierarchical configuration management
  - Environment variable integration
  - Configuration validation and default values

#### Command Line Interface (CLI)
- **`cli`**: Full CLI system development
  - Interactive command-line interface (`interface.py`)
  - Command processing and automation (`commands.py`)
  - User-friendly menu systems
  - Progress tracking and real-time feedback
  - Input validation and error handling

#### Data Layer Finalization
- **`data` (final modifications)**: Database optimization and refinement
  - Performance improvements and query optimization
  - Enhanced error handling and transaction management
  - Final data model adjustments and validation
  - Integration testing and bug fixes

#### Logging Infrastructure (Amazon)
- **`logs/amazon_scraper.log`**: Amazon-specific logging implementation
  - Advanced logging for Scrapy framework
  - Anti-bot detection logging
  - Performance metrics and error tracking

#### Documentation System
- **`docs`**: Comprehensive documentation creation
  - Technical architecture documentation
  - User guide and installation instructions
  - API reference documentation
  - README modernization and professional formatting


---

## 👨‍💻 Avto's Contributions

### **Primary Areas of Responsibility**

#### Core Scraping Implementations
- **Scraper Development** (except Scrapy framework):
  - `base_scraper.py`: Abstract base class and scraper interface
  - `static_scraper.py`: BeautifulSoup4 implementation for static content
  - `selenium_scraper.py`: Dynamic scraping with WebDriver
  - Anti-bot protection mechanisms
  - Error handling and retry logic

#### Testing Infrastructure
- **`tests`**: Complete testing framework implementation
  - Unit tests for core functionality (`test_statistics.py`)
  - Integration tests for end-to-end pipeline (`test_full_pipeline.py`)
  - Test configuration and fixtures
  - Continuous integration setup
  - Code coverage analysis and reporting

#### Data Analysis Engine
- **`analysis`**: Full analytical capabilities
  - Statistical analysis implementation (`statistics.py`)
  - Trend analysis and visualization (`trends.py`)
  - Professional report generation (`reports.py`)
  - Data quality assessment and validation
  - Chart generation with matplotlib and seaborn

#### Core Data Management
- **`data` (initial implementation)**: Foundation data layer
  - Database schema design and implementation
  - Data models and ORM-style classes
  - Data processing pipelines and validation
  - SQLite integration and optimization
  - Initial data persistence layer

#### Utility Functions
- **`utils`**: Core utility implementations
  - Configuration management helpers
  - Advanced logging setup with multiprocessing support
  - Helper functions for data processing
  - Request handling and HTTP utilities
  - Multiprocessing-safe logging queues

#### Logging Infrastructure (General)
- **`logs`** (excluding Amazon): General logging system
  - eBay scraper logging
  - BooksToScrape scraper logging
  - System-wide logging configuration
  - Log rotation and management

---


### Communication
- Regular progress updates and coordination
- Code review sessions and technical discussions
- Joint debugging and problem-solving
- Shared responsibility for project quality and deadlines

---

This project represents a true collaborative effort between us, Giorgi and Avto, with each contributor bringing unique strengths and taking ownership of critical components. The 50-50 contribution split reflects not just code volume, but equal responsibility, technical complexity, and project impact.

---

**Documentation**: Complete documentation available in the `docs/` directory  
**Contributors**: Giorgi (SakhelaTheInvincible) & Avto (Avtex19) 