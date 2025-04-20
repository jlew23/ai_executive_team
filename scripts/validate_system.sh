#!/bin/bash

# System validation script for AI Executive Team application
# This script checks all components of the system to ensure they are properly configured and working together

echo "Starting AI Executive Team system validation..."
echo "==============================================="

# Check directory structure
echo -e "\n[1/10] Checking directory structure..."
REQUIRED_DIRS=("agents" "knowledge_base" "llm" "slack" "web_dashboard" "utils" "tests" "docs")
MISSING_DIRS=0

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "/home/ubuntu/ai_executive_team/$dir" ]; then
    echo "❌ Missing directory: $dir"
    MISSING_DIRS=$((MISSING_DIRS+1))
  else
    echo "✅ Directory exists: $dir"
  fi
done

if [ $MISSING_DIRS -eq 0 ]; then
  echo "✅ All required directories are present."
else
  echo "❌ Missing $MISSING_DIRS required directories."
fi

# Check key files
echo -e "\n[2/10] Checking key files..."
REQUIRED_FILES=("main.py" "conversational_main.py" "simple_main.py" "run_api.py" "Dockerfile" "docker-compose.yml" "k8s-deployment.yml" "requirements.txt")
MISSING_FILES=0

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/$file" ]; then
    echo "❌ Missing file: $file"
    MISSING_FILES=$((MISSING_FILES+1))
  else
    echo "✅ File exists: $file"
  fi
done

if [ $MISSING_FILES -eq 0 ]; then
  echo "✅ All required files are present."
else
  echo "❌ Missing $MISSING_FILES required files."
fi

# Check agent implementations
echo -e "\n[3/10] Checking agent implementations..."
AGENT_FILES=("base_agent.py" "director_agent.py" "sales_agent.py" "marketing_agent.py" "finance_agent.py" "customer_service_agent.py" "technical_support_agent.py")
MISSING_AGENTS=0

for file in "${AGENT_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/agents/$file" ]; then
    echo "❌ Missing agent implementation: $file"
    MISSING_AGENTS=$((MISSING_AGENTS+1))
  else
    echo "✅ Agent implementation exists: $file"
  fi
done

if [ $MISSING_AGENTS -eq 0 ]; then
  echo "✅ All agent implementations are present."
else
  echo "❌ Missing $MISSING_AGENTS agent implementations."
fi

# Check knowledge base implementations
echo -e "\n[4/10] Checking knowledge base implementations..."
KB_FILES=("base.py" "document_processor.py" "vector_store.py" "version_manager.py")
MISSING_KB=0

for file in "${KB_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/knowledge_base/$file" ]; then
    echo "❌ Missing knowledge base implementation: $file"
    MISSING_KB=$((MISSING_KB+1))
  else
    echo "✅ Knowledge base implementation exists: $file"
  fi
done

if [ $MISSING_KB -eq 0 ]; then
  echo "✅ All knowledge base implementations are present."
else
  echo "❌ Missing $MISSING_KB knowledge base implementations."
fi

# Check LLM implementations
echo -e "\n[5/10] Checking LLM implementations..."
LLM_FILES=("base.py" "openai_provider.py" "anthropic_provider.py" "huggingface_provider.py" "local_provider.py" "prompt_template.py" "context_manager.py")
MISSING_LLM=0

for file in "${LLM_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/llm/$file" ]; then
    echo "❌ Missing LLM implementation: $file"
    MISSING_LLM=$((MISSING_LLM+1))
  else
    echo "✅ LLM implementation exists: $file"
  fi
done

if [ $MISSING_LLM -eq 0 ]; then
  echo "✅ All LLM implementations are present."
else
  echo "❌ Missing $MISSING_LLM LLM implementations."
fi

# Check Slack implementations
echo -e "\n[6/10] Checking Slack implementations..."
SLACK_FILES=("client.py" "event_handler.py" "message_formatter.py" "auth.py" "command_handler.py" "interactive_handler.py")
MISSING_SLACK=0

for file in "${SLACK_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/slack/$file" ]; then
    echo "❌ Missing Slack implementation: $file"
    MISSING_SLACK=$((MISSING_SLACK+1))
  else
    echo "✅ Slack implementation exists: $file"
  fi
done

if [ $MISSING_SLACK -eq 0 ]; then
  echo "✅ All Slack implementations are present."
else
  echo "❌ Missing $MISSING_SLACK Slack implementations."
fi

# Check web dashboard implementations
echo -e "\n[7/10] Checking web dashboard implementations..."
WEB_DIRS=("static" "templates" "routes" "models" "controllers")
MISSING_WEB_DIRS=0

for dir in "${WEB_DIRS[@]}"; do
  if [ ! -d "/home/ubuntu/ai_executive_team/web_dashboard/$dir" ]; then
    echo "❌ Missing web dashboard directory: $dir"
    MISSING_WEB_DIRS=$((MISSING_WEB_DIRS+1))
  else
    echo "✅ Web dashboard directory exists: $dir"
  fi
done

if [ $MISSING_WEB_DIRS -eq 0 ]; then
  echo "✅ All web dashboard directories are present."
else
  echo "❌ Missing $MISSING_WEB_DIRS web dashboard directories."
fi

# Check documentation
echo -e "\n[8/10] Checking documentation..."
DOC_FILES=("README.md" "api/README.md" "user/README.md" "developer/README.md" "architecture/README.md" "deployment/README.md")
MISSING_DOCS=0

for file in "${DOC_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/docs/$file" ]; then
    echo "❌ Missing documentation: $file"
    MISSING_DOCS=$((MISSING_DOCS+1))
  else
    echo "✅ Documentation exists: $file"
  fi
done

if [ $MISSING_DOCS -eq 0 ]; then
  echo "✅ All documentation files are present."
else
  echo "❌ Missing $MISSING_DOCS documentation files."
fi

# Check tests
echo -e "\n[9/10] Checking tests..."
TEST_DIRS=("unit" "integration" "e2e" "performance" "security")
MISSING_TEST_DIRS=0

for dir in "${TEST_DIRS[@]}"; do
  if [ ! -d "/home/ubuntu/ai_executive_team/tests/$dir" ]; then
    echo "❌ Missing test directory: $dir"
    MISSING_TEST_DIRS=$((MISSING_TEST_DIRS+1))
  else
    echo "✅ Test directory exists: $dir"
  fi
done

if [ $MISSING_TEST_DIRS -eq 0 ]; then
  echo "✅ All test directories are present."
else
  echo "❌ Missing $MISSING_TEST_DIRS test directories."
fi

# Check deployment configurations
echo -e "\n[10/10] Checking deployment configurations..."
DEPLOYMENT_FILES=("Dockerfile" "docker-compose.yml" "k8s-deployment.yml")
MISSING_DEPLOYMENT=0

for file in "${DEPLOYMENT_FILES[@]}"; do
  if [ ! -f "/home/ubuntu/ai_executive_team/$file" ]; then
    echo "❌ Missing deployment configuration: $file"
    MISSING_DEPLOYMENT=$((MISSING_DEPLOYMENT+1))
  else
    echo "✅ Deployment configuration exists: $file"
  fi
done

if [ $MISSING_DEPLOYMENT -eq 0 ]; then
  echo "✅ All deployment configurations are present."
else
  echo "❌ Missing $MISSING_DEPLOYMENT deployment configurations."
fi

# Calculate overall validation score
TOTAL_CHECKS=10
PASSED_CHECKS=$((TOTAL_CHECKS - (MISSING_DIRS > 0 ? 1 : 0) - (MISSING_FILES > 0 ? 1 : 0) - (MISSING_AGENTS > 0 ? 1 : 0) - (MISSING_KB > 0 ? 1 : 0) - (MISSING_LLM > 0 ? 1 : 0) - (MISSING_SLACK > 0 ? 1 : 0) - (MISSING_WEB_DIRS > 0 ? 1 : 0) - (MISSING_DOCS > 0 ? 1 : 0) - (MISSING_TEST_DIRS > 0 ? 1 : 0) - (MISSING_DEPLOYMENT > 0 ? 1 : 0)))
SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo -e "\n==============================================="
echo "Validation complete!"
echo "Score: $SCORE% ($PASSED_CHECKS/$TOTAL_CHECKS checks passed)"

if [ $SCORE -eq 100 ]; then
  echo "✅ All system components are properly implemented and configured."
  echo "The AI Executive Team application is ready for deployment."
else
  echo "⚠️ Some components need attention before deployment."
  echo "Please review the validation results above."
fi
