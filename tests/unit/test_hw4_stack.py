import aws_cdk as core
import aws_cdk.assertions as assertions

from hw4.hw4_stack import Hw4Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in hw4/hw4_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Hw4Stack(app, "hw4")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
