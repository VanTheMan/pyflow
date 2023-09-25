def step(unwrapped_step):

    def wrapped_step(*args):
        print("Hello, this is before function execution")

        print(f"The args to the function are: {args}")

        outputs = unwrapped_step(*args)

        print("This is after function execution")

        return outputs

    return wrapped_step


@step
def step1(x, y):
    print(f"step {x} {y}")
    return 1


@step
def step2(step1_output):
    print(step1_output)
    return 2


# step2_output = step2(step1(1, 2))
# step2_output.execute()

# Historical execution

# pf.step2(pf.step1(1, 2))
# step2(pf.step1.output1)