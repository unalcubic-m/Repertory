from django import forms


class AnswerForm(forms.Form):
    answer = forms.CharField(
        max_length=256,
        label="What did you hear?",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "autocapitalize": "none",
                "spellcheck": "false",
                "data-answer-input": "",
            }
        ),
    )
    replay_count = forms.IntegerField(
        min_value=0, max_value=100, initial=0, widget=forms.HiddenInput
    )


class RatingForm(forms.Form):
    rating = forms.TypedChoiceField(
        choices=((1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy")),
        coerce=int,
        widget=forms.RadioSelect,
    )
