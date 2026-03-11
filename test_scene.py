from manim import *

class TestScene(Scene):
    def construct(self):

        # VOICEOVER: Hello! AnimAI Studio is working correctly.
        text = Text("AnimAI Studio", font_size=64, color=BLUE)
        self.play(Write(text))
        self.wait(1)

        # VOICEOVER: Your Manim sandbox is ready to use.
        self.play(text.animate.set_color(GREEN).scale(1.2))
        self.wait(1)

        # VOICEOVER: Lets start building amazing animations.
        subtitle = Text("Sandbox Working!", font_size=32, color=WHITE)
        subtitle.next_to(text, DOWN, buff=0.5)
        self.play(FadeIn(subtitle))
        self.wait(2)