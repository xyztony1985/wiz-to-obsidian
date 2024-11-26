class WizTag(object):
    """ 为知笔记 TAG
    """

    # tag 的 guid
    guid: str = None
    parent_guid: str = None

    name: str = None

    nesting_name: str = None
    """
    嵌套的 tag 名称

    tag1/tag2/tag3/...
    """

    def __init__(self, guid, name, parent_guid=None) -> None:
        self.guid = guid
        self.name = name
        self.parent_guid = parent_guid

    @staticmethod
    def compute_nesting_name(tags: list['WizTag']) -> None:
        """ 计算嵌套名称 """
        for tag in tags:
            tag.nesting_name = tag.name
            if tag.parent_guid is None:
                continue
            parent_tag = next(t for t in tags if t.guid == tag.parent_guid)
            while parent_tag:
                if parent_tag.nesting_name:
                    tag.nesting_name = f"{parent_tag.nesting_name}/{tag.nesting_name}"
                    break
                tag.nesting_name = f"{parent_tag.name}/{tag.nesting_name}"
                parent_tag = next((t for t in tags if t.guid == parent_tag.parent_guid), None)

    def set_nesting_name(self, all_tags: list["WizTag"]):
        """ 

        Args:
            all_tags (list[&quot;WizTag&quot;]): 所有已经算好neting_name的所有tag的信息
        """
        self.nesting_name = next((tag.nesting_name for tag in all_tags if tag.guid == self.guid), self.name)
        return self
