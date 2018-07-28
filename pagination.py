def paginator(current_page, pages_count, paginator_length=None):
    items = list()
    if not paginator_length:
        paginator_length = pages_count
    icon = '<'   # '<' button
    page_link = str(current_page-1)
    if current_page == 1:
        status = 'disabled'
    else:
        status = ''
    items.append((icon, status, str(page_link)))
    for i in range(paginator_length):   # '1 2 3 .. ' buttons
        icon = str(i+1)
        page_link = icon
        if i == current_page-1:
            status = 'active'
        elif i >= pages_count:
            status = 'disabled'
        else:
            status = ''
        items.append((icon, status, page_link))
    icon = '>'  # '>' button
    page_link = current_page + 1
    if page_link > pages_count:
        status = 'disabled'
    else:
        status = ''
    items.append((icon, status, str(page_link)))
    return items


def pager(current_page, pages_count):
    items = []
    page_link = current_page - 1
    if page_link == 0:
        status = 'disabled'
        page_link = 1
    else:
        status = ''
    items.append((status, str(page_link)))
    page_link = current_page + 1
    if page_link > pages_count:
        status = 'disabled'
        page_link = pages_count
    else:
        status = ''
    items.append((status, str(page_link)))
    return items


def pages_count(list_len, max_items_per_page):
    p_count = list_len / max_items_per_page
    if int(p_count) == p_count:
        return int(p_count)
    else:
        return int(p_count) + 1
