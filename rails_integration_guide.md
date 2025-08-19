# ACI Rails Integration Guide

## Overview

This guide demonstrates how to integrate a Ruby on Rails application with the ACI.dev platform to provide users with access to 600+ integrations through natural language chat. The integration enables users to connect various services (Gmail, Slack, GitHub, etc.) from a single interface and interact with them conversationally.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Rails App     │    │   ACI Backend   │    │  External APIs  │
│                 │    │                 │    │                 │
│ - Chat UI       │◄──►│ - 600+ Apps     │◄──►│ - Gmail         │
│ - User Auth     │    │ - Function Exec │    │ - Slack         │
│ - Integration   │    │ - Semantic      │    │ - GitHub        │
│   Management    │    │   Search        │    │ - etc.          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core ACI Concepts

### Database Models
- **Project**: Multi-tenant container for API keys, apps, and agents
- **Agent**: Logical actor that accesses the platform (tied to API keys)
- **App**: Third-party service integrations (Gmail, Slack, etc.)
- **Function**: Individual API endpoints within apps
- **LinkedAccount**: User authentication credentials for OAuth/API keys
- **AppConfiguration**: User-specific app settings and permissions

### API Endpoints Structure
- **Base URL**: `https://api.aci.dev/v1`
- **Authentication**: API Key via `X-API-KEY` header
- **Key Endpoints**:
  - `/apps` - Browse available integrations
  - `/functions/search` - Semantic search for functions
  - `/functions/{function_name}/execute` - Execute functions
  - `/linked-accounts` - Manage user authentication
  - `/projects` - Project management

## Rails Implementation

### 1. Gemfile Dependencies

```ruby
# Gemfile
gem 'faraday', '~> 2.0'
gem 'faraday-retry', '~> 2.0'
gem 'redis', '~> 5.0'
gem 'sidekiq', '~> 7.0'
gem 'pg', '~> 1.1'

group :development, :test do
  gem 'rspec-rails'
  gem 'vcr'
  gem 'webmock'
end
```

### 2. Configuration

```ruby
# config/initializers/aci.rb
class AciConfig
  class << self
    def base_url
      ENV.fetch('ACI_BASE_URL', 'https://api.aci.dev/v1')
    end

    def api_key
      ENV.fetch('ACI_API_KEY') { raise 'ACI_API_KEY is required' }
    end

    def project_id
      ENV.fetch('ACI_PROJECT_ID') { raise 'ACI_PROJECT_ID is required' }
    end

    def redis_url
      ENV.fetch('REDIS_URL', 'redis://localhost:6379/0')
    end
  end
end
```

```ruby
# config/application.rb
config.cache_store = :redis_cache_store, { url: AciConfig.redis_url }
```

### 3. ACI Client Service

```ruby
# app/services/aci_client.rb
class AciClient
  include Singleton

  def initialize
    @client = Faraday.new(url: AciConfig.base_url) do |f|
      f.request :json
      f.request :retry, max: 3, interval: 0.5
      f.response :json
      f.adapter Faraday.default_adapter
      f.headers['X-API-KEY'] = AciConfig.api_key
      f.headers['Content-Type'] = 'application/json'
    end
  end

  # Get all available integrations
  def list_apps(limit: 50, offset: 0)
    response = @client.get('/apps') do |req|
      req.params[:limit] = limit
      req.params[:offset] = offset
    end
    handle_response(response)
  end

  # Search for integrations based on natural language intent
  def search_apps(intent:, limit: 10, include_functions: true)
    response = @client.get('/apps/search') do |req|
      req.params[:intent] = intent
      req.params[:limit] = limit
      req.params[:include_functions] = include_functions
    end
    handle_response(response)
  end

  # Get specific app details
  def get_app(app_name)
    response = @client.get("/apps/#{app_name}")
    handle_response(response)
  end

  # Search functions by natural language intent
  def search_functions(intent:, limit: 10, format: 'basic')
    response = @client.get('/functions/search') do |req|
      req.params[:intent] = intent
      req.params[:limit] = limit
      req.params[:format] = format
    end
    handle_response(response)
  end

  # Execute a function
  def execute_function(function_name, function_input, linked_account_owner_id)
    response = @client.post("/functions/#{function_name}/execute") do |req|
      req.body = {
        function_input: function_input,
        linked_account_owner_id: linked_account_owner_id
      }
    end
    handle_response(response)
  end

  # List user's linked accounts
  def list_linked_accounts(app_name: nil, linked_account_owner_id: nil)
    response = @client.get('/linked-accounts') do |req|
      req.params[:app_name] = app_name if app_name
      req.params[:linked_account_owner_id] = linked_account_owner_id if linked_account_owner_id
    end
    handle_response(response)
  end

  # Link OAuth2 account
  def link_oauth2_account(app_name, linked_account_owner_id, redirect_url = nil)
    response = @client.get('/linked-accounts/oauth2') do |req|
      req.params[:app_name] = app_name
      req.params[:linked_account_owner_id] = linked_account_owner_id
      req.params[:after_oauth2_link_redirect_url] = redirect_url if redirect_url
    end
    handle_response(response)
  end

  # Link API key account
  def link_api_key_account(app_name, linked_account_owner_id, api_key)
    response = @client.post('/linked-accounts/api-key') do |req|
      req.body = {
        app_name: app_name,
        linked_account_owner_id: linked_account_owner_id,
        api_key: api_key
      }
    end
    handle_response(response)
  end

  private

  def handle_response(response)
    case response.status
    when 200, 201
      response.body
    when 401
      raise AciError::Unauthorized, "Invalid API key"
    when 404
      raise AciError::NotFound, "Resource not found"
    when 422
      raise AciError::ValidationError, response.body['detail'] || "Validation error"
    when 429
      raise AciError::RateLimited, "Rate limit exceeded"
    else
      raise AciError::RequestFailed, "Request failed: #{response.status} #{response.body}"
    end
  end
end
```

### 4. Error Handling

```ruby
# app/services/aci_error.rb
module AciError
  class BaseError < StandardError; end
  class Unauthorized < BaseError; end
  class NotFound < BaseError; end
  class ValidationError < BaseError; end
  class RateLimited < BaseError; end
  class RequestFailed < BaseError; end
end
```

### 5. Models

```ruby
# app/models/user.rb
class User < ApplicationRecord
  has_many :aci_integrations, dependent: :destroy

  def aci_linked_account_owner_id
    # Use user ID as the linked account owner ID for ACI
    id.to_s
  end
end
```

```ruby
# app/models/aci_integration.rb
class AciIntegration < ApplicationRecord
  belongs_to :user

  validates :app_name, presence: true
  validates :linked_account_id, presence: true, uniqueness: { scope: :user_id }

  scope :active, -> { where(enabled: true) }

  def connected?
    linked_account_id.present? && enabled?
  end
end
```

```ruby
# Migration
class CreateAciIntegrations < ActiveRecord::Migration[7.0]
  def change
    create_table :aci_integrations do |t|
      t.references :user, null: false, foreign_key: true
      t.string :app_name, null: false
      t.string :linked_account_id
      t.boolean :enabled, default: true
      t.json :metadata, default: {}

      t.timestamps
    end

    add_index :aci_integrations, [:user_id, :app_name], unique: true
  end
end
```

### 6. Controllers

```ruby
# app/controllers/integrations_controller.rb
class IntegrationsController < ApplicationController
  before_action :authenticate_user!

  def index
    # Get all available integrations
    @available_apps = Rails.cache.fetch("aci_apps", expires_in: 1.hour) do
      AciClient.instance.list_apps(limit: 100)
    end

    # Get user's connected integrations
    @user_integrations = current_user.aci_integrations.includes(:user)
    
    # Get linked accounts from ACI
    @linked_accounts = AciClient.instance.list_linked_accounts(
      linked_account_owner_id: current_user.aci_linked_account_owner_id
    )
  rescue AciError::BaseError => e
    flash[:error] = "Failed to load integrations: #{e.message}"
    @available_apps = []
    @linked_accounts = []
  end

  def connect
    app_name = params[:app_name]
    
    # Get app details to determine authentication type
    app_details = AciClient.instance.get_app(app_name)
    security_schemes = app_details['security_schemes']

    if security_schemes.include?('oauth2')
      handle_oauth2_connection(app_name)
    elsif security_schemes.include?('api_key')
      render :api_key_form, locals: { app_name: app_name }
    else
      flash[:error] = "Unsupported authentication method"
      redirect_to integrations_path
    end
  rescue AciError::BaseError => e
    flash[:error] = "Failed to connect to #{app_name}: #{e.message}"
    redirect_to integrations_path
  end

  def connect_api_key
    app_name = params[:app_name]
    api_key = params[:api_key]

    result = AciClient.instance.link_api_key_account(
      app_name,
      current_user.aci_linked_account_owner_id,
      api_key
    )

    # Store integration locally
    current_user.aci_integrations.create!(
      app_name: app_name,
      linked_account_id: result['id'],
      enabled: true
    )

    flash[:success] = "Successfully connected to #{app_name}"
    redirect_to integrations_path
  rescue AciError::BaseError => e
    flash[:error] = "Failed to connect: #{e.message}"
    redirect_to integrations_path
  end

  def disconnect
    integration = current_user.aci_integrations.find(params[:id])
    
    # Delete from ACI
    AciClient.instance.delete_linked_account(integration.linked_account_id)
    
    # Delete locally
    integration.destroy!

    flash[:success] = "Integration disconnected successfully"
    redirect_to integrations_path
  rescue AciError::BaseError => e
    flash[:error] = "Failed to disconnect: #{e.message}"
    redirect_to integrations_path
  end

  private

  def handle_oauth2_connection(app_name)
    redirect_url = oauth2_callback_url(app_name: app_name)
    
    result = AciClient.instance.link_oauth2_account(
      app_name,
      current_user.aci_linked_account_owner_id,
      redirect_url
    )

    redirect_to result['url'], allow_other_host: true
  end
end
```

```ruby
# app/controllers/chat_controller.rb
class ChatController < ApplicationController
  before_action :authenticate_user!

  def index
    @messages = []
  end

  def send_message
    message = params[:message]
    
    # Process the message and execute functions
    response = ChatService.new(current_user).process_message(message)
    
    render json: { response: response }
  rescue StandardError => e
    render json: { error: e.message }, status: 422
  end
end
```

### 7. Chat Service with Natural Language Processing

```ruby
# app/services/chat_service.rb
class ChatService
  def initialize(user)
    @user = user
    @aci_client = AciClient.instance
  end

  def process_message(message)
    # Step 1: Determine intent and search for relevant functions
    relevant_functions = search_functions_for_message(message)
    
    return "I couldn't find any relevant integrations for that request." if relevant_functions.empty?

    # Step 2: Check if user has required integrations connected
    missing_integrations = check_required_integrations(relevant_functions)
    
    if missing_integrations.any?
      return build_connection_prompt(missing_integrations)
    end

    # Step 3: Execute the most relevant function
    execute_best_function(relevant_functions.first, message)
  rescue AciError::BaseError => e
    "Sorry, I encountered an error: #{e.message}"
  end

  private

  def search_functions_for_message(message)
    @aci_client.search_functions(
      intent: message,
      limit: 5,
      format: 'basic'
    )
  end

  def check_required_integrations(functions)
    required_apps = functions.map { |f| extract_app_name(f['name']) }.uniq
    connected_apps = @user.aci_integrations.active.pluck(:app_name)
    
    required_apps - connected_apps
  end

  def extract_app_name(function_name)
    # Function names are formatted as "APP_NAME__FUNCTION_NAME"
    function_name.split('__').first
  end

  def build_connection_prompt(missing_apps)
    app_list = missing_apps.map { |app| "`#{app}`" }.join(', ')
    
    "To perform this action, you'll need to connect the following integrations: #{app_list}. " \
    "Would you like me to help you set them up?"
  end

  def execute_best_function(function, original_message)
    app_name = extract_app_name(function['name'])
    
    # Extract parameters from message (simplified - you might want to use LLM for this)
    params = extract_parameters_from_message(function, original_message)
    
    result = @aci_client.execute_function(
      function['name'],
      params,
      @user.aci_linked_account_owner_id
    )

    format_execution_result(result, function)
  end

  def extract_parameters_from_message(function, message)
    # Simplified parameter extraction
    # In production, you'd want to use an LLM to extract structured data
    case function['name']
    when /GMAIL__SEND_EMAIL/
      extract_email_params(message)
    when /SLACK__SEND_MESSAGE/
      extract_slack_params(message)
    else
      {}
    end
  end

  def extract_email_params(message)
    # Very basic email parameter extraction
    # You'd want to use regex or LLM for better extraction
    {
      sender: "me",
      recipient: extract_email_from_message(message),
      subject: extract_subject_from_message(message),
      body: message
    }
  end

  def extract_email_from_message(message)
    # Extract email using regex
    email_regex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
    message.match(email_regex)&.to_s || ""
  end

  def extract_subject_from_message(message)
    # Extract subject line (very basic)
    if message.include?("subject:")
      message.split("subject:").last.split("\n").first.strip
    else
      "Message from chat"
    end
  end

  def format_execution_result(result, function)
    if result['success']
      case function['name']
      when /EMAIL/
        "✅ Email sent successfully!"
      when /SLACK/
        "✅ Slack message sent!"
      else
        "✅ Action completed successfully!"
      end
    else
      "❌ Action failed: #{result['error']}"
    end
  end
end
```

### 8. OAuth2 Callback Handling

```ruby
# config/routes.rb
Rails.application.routes.draw do
  root 'chat#index'
  
  resources :integrations do
    member do
      delete :disconnect
    end
    collection do
      post :connect
      post :connect_api_key
      get 'oauth2_callback/:app_name', to: 'integrations#oauth2_callback', as: :oauth2_callback
    end
  end

  resources :chat, only: [:index] do
    collection do
      post :send_message
    end
  end
end
```

```ruby
# app/controllers/integrations_controller.rb (additional method)
def oauth2_callback
  app_name = params[:app_name]
  
  # The ACI backend handles the OAuth2 flow and creates the linked account
  # We just need to record it locally
  linked_accounts = AciClient.instance.list_linked_accounts(
    app_name: app_name,
    linked_account_owner_id: current_user.aci_linked_account_owner_id
  )

  if linked_accounts.any?
    linked_account = linked_accounts.last
    
    current_user.aci_integrations.create!(
      app_name: app_name,
      linked_account_id: linked_account['id'],
      enabled: true
    )

    flash[:success] = "Successfully connected to #{app_name}!"
  else
    flash[:error] = "Failed to complete OAuth2 connection"
  end

  redirect_to integrations_path
end
```

### 9. Views

```erb
<!-- app/views/integrations/index.html.erb -->
<div class="container mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">Your Integrations</h1>
  
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <% @available_apps.each do |app| %>
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center mb-4">
          <% if app['logo'] %>
            <img src="<%= app['logo'] %>" alt="<%= app['display_name'] %>" class="w-10 h-10 mr-3">
          <% end %>
          <h3 class="text-lg font-semibold"><%= app['display_name'] %></h3>
        </div>
        
        <p class="text-gray-600 mb-4"><%= app['description'] %></p>
        
        <% if @linked_accounts.any? { |la| la['app']['name'] == app['name'] } %>
          <div class="flex items-center justify-between">
            <span class="text-green-600 font-medium">✅ Connected</span>
            <% integration = @user_integrations.find { |i| i.app_name == app['name'] } %>
            <% if integration %>
              <%= link_to "Disconnect", integration, method: :delete, 
                          class: "text-red-600 hover:text-red-800",
                          confirm: "Are you sure you want to disconnect from #{app['display_name']}?" %>
            <% end %>
          </div>
        <% else %>
          <%= link_to "Connect", connect_integrations_path(app_name: app['name']), 
                      method: :post, 
                      class: "bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700" %>
        <% end %>
      </div>
    <% end %>
  </div>
</div>
```

```erb
<!-- app/views/chat/index.html.erb -->
<div class="container mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">AI Assistant</h1>
  
  <div id="chat-container" class="bg-white rounded-lg shadow-md p-6 mb-4 h-96 overflow-y-auto">
    <div id="messages"></div>
  </div>
  
  <%= form_with url: send_message_chat_index_path, method: :post, remote: true, local: false, id: "chat-form" do |f| %>
    <div class="flex">
      <%= f.text_field :message, placeholder: "Send an email to john@example.com about the meeting...", 
                       class: "flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" %>
      <%= f.submit "Send", class: "bg-blue-600 text-white px-6 py-2 rounded-r-lg hover:bg-blue-700" %>
    </div>
  <% end %>
</div>

<script>
document.getElementById('chat-form').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const formData = new FormData(this);
  const message = formData.get('message');
  
  if (!message.trim()) return;
  
  // Add user message to chat
  addMessage('user', message);
  
  // Clear input
  document.getElementById('message').value = '';
  
  // Send to backend
  fetch('<%= send_message_chat_index_path %>', {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRF-Token': document.querySelector('[name="csrf-token"]').content
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.response) {
      addMessage('assistant', data.response);
    } else if (data.error) {
      addMessage('assistant', 'Error: ' + data.error);
    }
  })
  .catch(error => {
    addMessage('assistant', 'Sorry, something went wrong.');
  });
});

function addMessage(sender, message) {
  const messagesDiv = document.getElementById('messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `mb-4 ${sender === 'user' ? 'text-right' : 'text-left'}`;
  
  messageDiv.innerHTML = `
    <div class="inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
      sender === 'user' 
        ? 'bg-blue-600 text-white' 
        : 'bg-gray-200 text-gray-800'
    }">
      ${message}
    </div>
  `;
  
  messagesDiv.appendChild(messageDiv);
  
  // Scroll to bottom
  const container = document.getElementById('chat-container');
  container.scrollTop = container.scrollHeight;
}
</script>
```

### 10. Background Jobs for Async Processing

```ruby
# app/jobs/function_execution_job.rb
class FunctionExecutionJob < ApplicationJob
  queue_as :default

  def perform(user_id, function_name, function_input, chat_session_id)
    user = User.find(user_id)
    
    result = AciClient.instance.execute_function(
      function_name,
      function_input,
      user.aci_linked_account_owner_id
    )

    # Broadcast result back to user via ActionCable
    ActionCable.server.broadcast(
      "chat_#{user_id}",
      {
        type: 'function_result',
        session_id: chat_session_id,
        result: result
      }
    )
  rescue StandardError => e
    ActionCable.server.broadcast(
      "chat_#{user_id}",
      {
        type: 'error',
        session_id: chat_session_id,
        message: e.message
      }
    )
  end
end
```

### 11. Caching Strategy

```ruby
# app/services/aci_cache_service.rb
class AciCacheService
  CACHE_EXPIRES = {
    apps: 1.hour,
    functions: 30.minutes,
    linked_accounts: 5.minutes
  }.freeze

  class << self
    def cached_apps
      Rails.cache.fetch("aci:apps", expires_in: CACHE_EXPIRES[:apps]) do
        AciClient.instance.list_apps(limit: 200)
      end
    end

    def cached_user_linked_accounts(user_id)
      Rails.cache.fetch(
        "aci:linked_accounts:#{user_id}", 
        expires_in: CACHE_EXPIRES[:linked_accounts]
      ) do
        user = User.find(user_id)
        AciClient.instance.list_linked_accounts(
          linked_account_owner_id: user.aci_linked_account_owner_id
        )
      end
    end

    def invalidate_user_cache(user_id)
      Rails.cache.delete("aci:linked_accounts:#{user_id}")
    end
  end
end
```

### 12. Testing

```ruby
# spec/services/aci_client_spec.rb
RSpec.describe AciClient do
  let(:client) { described_class.instance }

  describe '#list_apps' do
    it 'returns available apps' do
      VCR.use_cassette('aci/list_apps') do
        result = client.list_apps(limit: 10)
        
        expect(result).to be_an(Array)
        expect(result.first).to include('name', 'display_name', 'description')
      end
    end
  end

  describe '#search_functions' do
    it 'finds relevant functions for email intent' do
      VCR.use_cassette('aci/search_functions_email') do
        result = client.search_functions(intent: 'send an email', limit: 5)
        
        expect(result).to be_an(Array)
        expect(result.any? { |f| f['name'].include?('EMAIL') }).to be true
      end
    end
  end
end
```

```ruby
# spec/services/chat_service_spec.rb
RSpec.describe ChatService do
  let(:user) { create(:user) }
  let(:service) { described_class.new(user) }

  describe '#process_message' do
    context 'when user has required integrations' do
      before do
        create(:aci_integration, user: user, app_name: 'GMAIL')
      end

      it 'processes email sending request' do
        VCR.use_cassette('aci/send_email') do
          result = service.process_message('send an email to john@example.com')
          
          expect(result).to include('Email sent successfully')
        end
      end
    end

    context 'when user lacks required integrations' do
      it 'prompts to connect integrations' do
        result = service.process_message('send an email to john@example.com')
        
        expect(result).to include('connect the following integrations')
        expect(result).to include('GMAIL')
      end
    end
  end
end
```

## Deployment Considerations

### Environment Variables
```bash
# .env
ACI_BASE_URL=https://api.aci.dev/v1
ACI_API_KEY=your_api_key_here
ACI_PROJECT_ID=your_project_id_here
REDIS_URL=redis://localhost:6379/0
```

### Docker Compose (Development)
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - ACI_API_KEY=${ACI_API_KEY}
      - ACI_PROJECT_ID=${ACI_PROJECT_ID}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=myapp_development
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  sidekiq:
    build: .
    command: bundle exec sidekiq
    environment:
      - ACI_API_KEY=${ACI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

### Production Deployment
- Use environment variables for ACI credentials
- Implement proper error monitoring (Sentry, etc.)
- Set up Redis for caching and background jobs
- Configure rate limiting for API calls
- Use SSL/TLS for all communications
- Implement proper logging for audit trails

## Advanced Features

### 1. Function Chaining
```ruby
class ChatService
  def process_complex_message(message)
    # Example: "Get my emails and summarize them in Slack"
    functions = search_and_chain_functions(message)
    
    functions.each_with_index do |function, index|
      result = execute_function_with_context(function, message, previous_results)
      store_intermediate_result(result, index)
    end
  end
end
```

### 2. Custom Instructions
Configure custom instructions for agents to modify function behavior based on user preferences.

### 3. Quota Management
Monitor and manage API usage quotas per user to prevent abuse.

### 4. Webhook Support
Set up webhooks to receive real-time updates from connected services.

## Security Best Practices

1. **API Key Management**: Store ACI API keys securely using Rails credentials
2. **User Data**: Never log sensitive user data or API responses
3. **Rate Limiting**: Implement client-side rate limiting to respect ACI limits
4. **Input Validation**: Validate all user inputs before sending to ACI
5. **Error Handling**: Don't expose internal errors to users
6. **HTTPS Only**: Always use HTTPS for production deployments

## Monitoring and Analytics

- Track integration usage patterns
- Monitor API response times and error rates
- Set up alerts for failed function executions
- Implement user activity logging for audit purposes

This implementation provides a complete foundation for integrating Rails with ACI.dev, enabling users to connect multiple services and interact with them through natural language in a single chat interface.