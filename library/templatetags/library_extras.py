from django import template

from library.forms import format_timecode

register = template.Library()


@register.filter
def timecode(milliseconds: int) -> str:
    return format_timecode(milliseconds)
