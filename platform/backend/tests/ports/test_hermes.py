from agentic_platform.ports.hermes import (
    ChannelDescriptor,
    DescriptorSource,
    ProviderDescriptor,
    ProviderIdentityKind,
    ToolDescriptor,
)


def test_hermes_descriptors_keep_identity_families_separate() -> None:
    channel = ChannelDescriptor(
        platform_id="telegram",
        display_name="Telegram",
        source=DescriptorSource.PLUGIN,
        capabilities=frozenset({"messages", "threads", "reactions"}),
        deferred=True,
    )
    api_key_provider = ProviderDescriptor(
        provider_id="openai-api",
        display_name="OpenAI API",
        identity_kind=ProviderIdentityKind.AUTH,
        aliases=frozenset({"openai"}),
    )
    transport = ProviderDescriptor(
        provider_id="openai",
        display_name="OpenAI-compatible transport",
        identity_kind=ProviderIdentityKind.TRANSPORT,
    )
    tool = ToolDescriptor(
        name="web_search",
        toolset="web",
        source=DescriptorSource.BUILTIN,
        risk_class="external_write",
    )

    assert channel.deferred is True
    assert api_key_provider != transport
    assert api_key_provider.identity_kind is ProviderIdentityKind.AUTH
    assert transport.identity_kind is ProviderIdentityKind.TRANSPORT
    assert tool.toolset == "web"
