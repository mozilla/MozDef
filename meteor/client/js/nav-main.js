$(document).ready(function() {
    if ($('#nav-main').length === 0) {
        return;
    }

    var main_menuitems = $('#nav-main [tabindex="0"]');
    var prev_li, new_li, focused_item;

    $('#nav-main > li').bind('mouseover focusin', function(event) {
        new_li = $(this);
        if (!prev_li || prev_li.attr('id') !== new_li.attr('id')) {
            // Open the menu
            new_li.addClass('hover').find('[role="menu"]').attr('aria-expanded', 'true');
            if (prev_li) {
                // Close the last selected menu
                prev_li.dequeue();
            }
        } else {
            prev_li.clearQueue();
        }
    }).bind('mouseout focusout', function(event) {
        prev_li = $(this);
        prev_li.delay(100).queue(function() {
            if (prev_li) {
                prev_li.clearQueue();
                // Close the menu
                prev_li.removeClass('hover').find('[role="menu"]').attr('aria-expanded', 'false');
                prev_li = null;
                if (focused_item) {
                    focused_item.get(0).blur();
                }
            }
        });
    }).each(function(menu_idx) {
        var menu = $(this).find('[role="menu"]');
        var menuitems = $(this).find('a');

        menuitems.mouseover(function(event) {
            this.focus(); // Sometimes $(this).focus() doesn"t work
        }).focus(function() {
            focused_item = $(this);
        }).each(function(item_idx) {
            // Enable keyboard navigation
            $(this).keydown(function(event) {
                var target;
                switch (event.keyCode) {
                    case 33: // Page Up
                    case 36: // Home
                        target = menuitems.first();
                        break;
                    case 34: // Page Down
                    case 35: // End
                        target = menuitems.last();
                        break;
                    case 38: // Up
                        target = (item_idx > 0) ? menuitems.eq(item_idx - 1)
                            : menuitems.last();
                        break;
                    case 40: // Down
                        target = (item_idx < menuitems.length - 1) ? menuitems.eq(item_idx + 1)
                            : menuitems.first();
                        break;
                    case 37: // Left
                        target = (menu_idx > 0) ? main_menuitems.eq(menu_idx - 1)
                            : main_menuitems.last();
                        break;
                    case 39: // Right
                        target = (menu_idx < main_menuitems.length - 1) ? main_menuitems.eq(menu_idx + 1)
                            : main_menuitems.first();
                        break;
                }
                if (target) {
                    target.get(0).focus(); // Sometimes target.focus() doesn't work
                    return false;
                }
                return true;
            });
        });
    });

    // With JavaScript enabled, we can provide a full navigation with #nav-main.
    // Now "hide" the duplicated #footer-menu from AT.
    $('#footer-menu').attr('role', 'presentation');
});

