require 'spec_helper'

describe User do

  it { should respond_to :display_name }
  it { should validate_length_of(:display_name).length(100) }
  it { should validate_presence_of(:display_name) }

  it { should respond_to :login }
  it { should validate_presence_of(:login) }
  it { should validate_length_of(:login).max(10) }
end
