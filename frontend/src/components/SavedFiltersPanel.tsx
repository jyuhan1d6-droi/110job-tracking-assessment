import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { Alert, Button, Card, Empty, Form, Input, List, message, Modal, Space, Tag, Typography } from "antd";
import { createSavedFilter, deleteSavedFilter, fetchSavedFilters, updateSavedFilter } from "../api/savedFilters";
import type { SavedFilter, SavedFilterInput } from "../types/savedFilters";

type Props = {
  keyword: string;
  city: string;
  activeId: string;
  onUse: (filter: SavedFilter) => void;
  onDeletedActive: () => void;
};

function errorText(error: unknown) {
  if (error instanceof AxiosError) return error.response?.data?.detail ?? "操作失败，请稍后重试";
  return "操作失败，请稍后重试";
}

export function buildSavedFilterParams(filter: SavedFilter) {
  const next: Record<string, string> = { savedFilter: filter.id };
  if (filter.keyword) next.keyword = filter.keyword;
  if (filter.city) next.city = filter.city;
  return next;
}

export default function SavedFiltersPanel({ keyword, city, activeId, onUse, onDeletedActive }: Props) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<SavedFilter | null>(null);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<SavedFilterInput>();
  const savedFilters = useQuery({ queryKey: ["saved-filters"], queryFn: fetchSavedFilters });

  const save = useMutation({
    mutationFn: (values: SavedFilterInput) => editing
      ? updateSavedFilter(editing.id, values)
      : createSavedFilter(values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["saved-filters"] });
      message.success(editing ? "筛选方案已更新" : "筛选方案已保存");
      setOpen(false);
      setEditing(null);
      form.resetFields();
    },
  });
  const remove = useMutation({
    mutationFn: deleteSavedFilter,
    onSuccess: async (_, id) => {
      await queryClient.invalidateQueries({ queryKey: ["saved-filters"] });
      if (id === activeId) onDeletedActive();
      message.success("筛选方案已删除，当前搜索条件保持不变");
    },
    onError: error => message.error(errorText(error)),
  });

  function showCreate() {
    setEditing(null);
    form.setFieldsValue({ name: "", keyword: keyword || null, city: city || null });
    setOpen(true);
  }

  function showEdit(item: SavedFilter) {
    setEditing(item);
    form.setFieldsValue({ name: item.name, keyword: item.keyword, city: item.city });
    setOpen(true);
  }

  function confirmDelete(item: SavedFilter) {
    Modal.confirm({
      title: `删除“${item.name}”？`,
      content: "只删除收藏的筛选方案，不会删除岗位或改变当前搜索结果。",
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: () => remove.mutateAsync(item.id),
    });
  }

  return <Card title="筛选方案" extra={<Button type="primary" disabled={!keyword && !city} onClick={showCreate}>保存当前条件</Button>}>
    {savedFilters.isError && <Alert type="error" showIcon message="加载筛选方案失败" action={<Button onClick={() => savedFilters.refetch()}>重试</Button>} />}
    {!savedFilters.isError && <List
      loading={savedFilters.isLoading}
      locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有保存筛选方案" /> }}
      dataSource={savedFilters.data ?? []}
      renderItem={item => <List.Item actions={[
        <Button type="link" onClick={() => onUse(item)}>使用</Button>,
        <Button type="link" onClick={() => showEdit(item)}>编辑</Button>,
        <Button type="link" danger onClick={() => confirmDelete(item)}>删除</Button>,
      ]}>
        <List.Item.Meta
          title={<Space>{item.name}{item.id === activeId && <Tag color="green">正在使用</Tag>}</Space>}
          description={<Space wrap><Typography.Text type="secondary">关键词：{item.keyword || "不限"}</Typography.Text><Typography.Text type="secondary">城市：{item.city || "不限"}</Typography.Text></Space>}
        />
      </List.Item>}
    />}
    <Modal
      title={editing ? "编辑筛选方案" : "保存筛选方案"}
      open={open}
      confirmLoading={save.isPending}
      okText={editing ? "保存修改" : "保存"}
      cancelText="取消"
      onCancel={() => { setOpen(false); setEditing(null); save.reset(); }}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" onFinish={values => save.mutate(values)}>
        <Form.Item name="name" label="方案名称" rules={[{ required: true, whitespace: true, message: "请输入方案名称" }, { max: 100 }]}><Input maxLength={100} /></Form.Item>
        <Form.Item name="keyword" label="关键词" rules={[{ max: 200 }]}><Input allowClear maxLength={200} placeholder="岗位名称或岗位要求" /></Form.Item>
        <Form.Item name="city" label="城市" rules={[{ max: 100 }]}><Input allowClear maxLength={100} placeholder="来源显示的城市" /></Form.Item>
        {!Form.useWatch("keyword", form)?.trim() && !Form.useWatch("city", form)?.trim() && <Alert type="warning" message="关键词和城市不能同时为空" />}
        {save.isError && <Alert className="inline-alert" type="error" showIcon message={errorText(save.error)} />}
      </Form>
    </Modal>
  </Card>;
}
