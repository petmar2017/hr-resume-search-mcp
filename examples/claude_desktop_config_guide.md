# Claude Desktop MCP Configuration Guide

**Complete guide for integrating HR Resume Search MCP server with Claude Desktop**

## 📋 Overview

This guide provides step-by-step instructions for configuring the HR Resume Search MCP server to work with Claude Desktop, enabling powerful resume search and analysis capabilities directly within your Claude conversations.

## 🎯 Features Available

Once configured, you'll have access to these powerful tools:

- **🔍 Similar Resume Search** - Find candidates with similar profiles
- **🏢 Department Search** - Discover candidates by department and company
- **🤝 Colleague Discovery** - Find professional network connections
- **🧠 Smart Natural Language Queries** - AI-powered resume search
- **📊 Network Analysis** - Analyze professional relationships
- **📈 Database Statistics** - Get insights about your resume database

---

## 🛠️ Prerequisites

### System Requirements
- **Claude Desktop** - Latest version installed
- **Python 3.12+** - Required for MCP server
- **Git** - For repository management
- **Terminal/Command Prompt** - For running setup commands

### Project Setup
```bash
# Clone the repository
git clone <repository-url>
cd api_builder/workspace

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r mcp_server/requirements.txt
```

---

## ⚙️ Configuration Steps

### Step 1: Locate Claude Desktop Configuration

Claude Desktop stores its configuration in different locations based on your operating system:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Create/Edit Configuration File

If the file doesn't exist, create it. If it exists, add the HR Resume Search MCP server configuration:

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/api_builder/workspace",
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/hr_resumes",
        "REDIS_URL": "redis://localhost:6379",
        "CLAUDE_API_KEY": "${CLAUDE_API_KEY}"
      }
    }
  }
}
```

### Step 3: Update Configuration Paths

**CRITICAL:** Update the `PYTHONPATH` with your actual project path:

```bash
# Get your current directory
pwd
# Copy the output and use it in the PYTHONPATH
```

Example configurations for different setups:

**For Development (SQLite):**
```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/Users/yourname/projects/api_builder/workspace",
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "sqlite:///./hr_resume_db.sqlite",
        "ENVIRONMENT": "development"
      }
    }
  }
}
```

**For Production (PostgreSQL):**
```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/home/user/api_builder/workspace",
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://hr_user:secure_password@localhost:5432/hr_resumes",
        "REDIS_URL": "redis://localhost:6379",
        "CLAUDE_API_KEY": "your-claude-api-key-here",
        "ENVIRONMENT": "production"
      }
    }
  }
}
```

### Step 4: Environment Variables Setup

Create a `.env` file in your workspace directory:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your actual values
nano .env
```

Example `.env` configuration:
```bash
# Application
APP_NAME=hr-resume-search-mcp
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./hr_resume_db.sqlite
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/hr_resumes

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Claude AI
CLAUDE_API_KEY=your-claude-api-key-here

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Testing the Configuration

### Step 1: Test MCP Server Directly

Before configuring Claude Desktop, test the MCP server:

```bash
# Navigate to your project directory
cd /path/to/api_builder/workspace

# Activate virtual environment
source venv/bin/activate

# Test MCP server
python -m mcp_server.server
```

You should see output like:
```
INFO - Starting MCP server...
INFO - HR tools registered successfully
INFO - MCP Server ready for connections
```

### Step 2: Test with Claude Desktop

1. **Restart Claude Desktop** after saving the configuration
2. **Open a new conversation**
3. **Test the connection** with a simple query:

```
Can you check if the HR resume search tools are available?
```

Claude should respond with available tools like:
- `search_similar_resumes`
- `search_by_department`
- `find_colleagues`
- `smart_query_resumes`
- `analyze_resume_network`
- `get_resume_statistics`

### Step 3: Test Tool Functionality

Try these example queries to test different tools:

**Database Statistics:**
```
Can you get statistics about the resume database?
```

**Department Search:**
```
Find all candidates who worked in the Engineering department at TechCorp
```

**Smart Search:**
```
Find me Python developers with 5+ years experience in fintech companies
```

**Similar Candidates:**
```
Find candidates similar to John Doe based on skills and experience
```

---

## 🔧 Advanced Configuration

### Custom Tool Parameters

You can customize the MCP server behavior by adding parameters to the configuration:

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/path/to/workspace",
        "LOG_LEVEL": "DEBUG",
        "MAX_SEARCH_RESULTS": "50",
        "SIMILARITY_THRESHOLD": "0.7",
        "ENABLE_CACHING": "true",
        "CACHE_TTL": "300"
      }
    }
  }
}
```

### Multiple Database Configurations

For multiple environments or databases:

```json
{
  "mcpServers": {
    "hr-resume-search-dev": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/path/to/workspace",
        "DATABASE_URL": "sqlite:///./dev_hr_resumes.db",
        "ENVIRONMENT": "development"
      }
    },
    "hr-resume-search-prod": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/path/to/workspace",
        "DATABASE_URL": "postgresql://user:pass@prod-server:5432/hr_resumes",
        "ENVIRONMENT": "production"
      }
    }
  }
}
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Issue: "MCP server not found"
**Solution:**
1. Check that `PYTHONPATH` is correct
2. Verify Python virtual environment is activated
3. Ensure all dependencies are installed

#### Issue: "Permission denied"
**Solution:**
1. Check file permissions on the workspace directory
2. Ensure Python executable is accessible
3. Verify environment variables are set correctly

#### Issue: "Database connection failed"
**Solution:**
1. Verify `DATABASE_URL` is correct
2. Check database server is running
3. Verify user permissions for database access

#### Issue: "Tools not appearing in Claude"
**Solution:**
1. Restart Claude Desktop after configuration changes
2. Check the MCP server logs for errors
3. Verify JSON configuration syntax is valid

### Debug Mode

Enable debug logging for troubleshooting:

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "/path/to/workspace"
      }
    }
  }
}
```

### Log Files

Check these locations for logs:
- **MCP Server Logs:** Console output when running the server directly
- **Claude Desktop Logs:** Available through Claude Desktop's debug menu
- **Application Logs:** Check your project's `logs/` directory if configured

---

## 🎯 Usage Examples

Once configured, you can use these powerful queries in Claude Desktop:

### Professional Network Analysis
```
Analyze the professional network for candidates who worked at TechCorp and StartupXYZ. Show me the connections and overlapping time periods.
```

### Smart Recruitment Queries
```
I need to find senior data scientists with experience in machine learning and fintech. They should have worked at companies similar to our target market.
```

### Colleague Discovery
```
For candidate John Smith (ID: candidate_123), find all his former colleagues who might be good referrals for our engineering team.
```

### Department Insights
```
Give me statistics about all candidates in our database who worked in Product Management roles, including their skills distribution and company backgrounds.
```

---

## 📊 Performance Optimization

### Caching Configuration
```json
{
  "env": {
    "ENABLE_CACHING": "true",
    "CACHE_TTL": "600",
    "MAX_CACHE_SIZE": "1000"
  }
}
```

### Database Optimization
```bash
# For PostgreSQL, create indexes
CREATE INDEX idx_candidates_department ON candidates USING gin ((resume_data->'experience'));
CREATE INDEX idx_candidates_skills ON candidates USING gin ((resume_data->'skills'));
```

### Connection Pooling
```json
{
  "env": {
    "DATABASE_POOL_SIZE": "20",
    "DATABASE_MAX_OVERFLOW": "40"
  }
}
```

---

## 🔐 Security Considerations

### API Keys
- Store sensitive keys in environment variables
- Use `${VARIABLE_NAME}` syntax in configuration
- Never commit API keys to version control

### Database Security
- Use strong passwords for database connections
- Enable SSL/TLS for database connections
- Restrict database access to specific IP addresses

### Network Security
- Run MCP server on localhost only
- Use VPN for remote database connections
- Implement rate limiting if needed

---

## 📚 Additional Resources

### Documentation Links
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop Documentation](https://docs.anthropic.com/claude/docs)
- [Project API Documentation](../docs/api_reference.md)

### Example Configurations
- [Basic Configuration](../mcp_server/claude_desktop_config.json)
- [Advanced Configuration](../examples/advanced_claude_config.json)
- [Production Configuration](../examples/production_claude_config.json)

### Support
- **GitHub Issues:** Report bugs and request features
- **Documentation:** Check project README and API docs
- **Community:** Join discussions in project discussions

---

## ✅ Verification Checklist

Before considering your setup complete, verify:

- [ ] MCP server starts without errors
- [ ] Claude Desktop recognizes the server
- [ ] All 6 HR tools are available in Claude
- [ ] Database connection works
- [ ] Test queries return expected results
- [ ] Error handling works correctly
- [ ] Performance is acceptable
- [ ] Logs show proper operation

---

**🎉 Congratulations!** Your HR Resume Search MCP server is now integrated with Claude Desktop. You can now leverage powerful resume search and analysis capabilities directly in your Claude conversations!