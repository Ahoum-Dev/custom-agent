import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LLMConfig } from '@/lib/types';
import Link from 'next/link';

export default function LLMConfigPage() {
    const [activeTab, setActiveTab] = useState<'create' | 'configure'>('configure');
    const [config, setConfig] = useState<LLMConfig>({
        name: '',
        description: '',
        instructions: '',
        conversationStarters: [
            'How can I improve my website\'s SEO?',
            'What are the latest SEO trends?',
            'Can you analyze my website\'s SEO?',
            'How to do keyword research effectively?',
            ''
        ],
        capabilities: {
            webBrowsing: false,
            imageGeneration: false,
            codeInterpreter: false
        },
        actions: []
    });
    const [savedConfigs, setSavedConfigs] = useState<LLMConfig[]>([]);
    const [loading, setLoading] = useState(false);

    // Load saved configurations on page load
    useEffect(() => {
        loadConfigurations();
    }, []);

    const loadConfigurations = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/llm-config');
            const result = await response.json();

            if (result.success && Array.isArray(result.data)) {
                setSavedConfigs(result.data);
            }
        } catch (error) {
            console.error('Error loading configurations:', error);
            alert('Failed to load configurations. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const loadConfiguration = async (name: string) => {
        try {
            setLoading(true);
            const response = await fetch(`/api/llm-config?name=${name}`);
            const result = await response.json();

            if (result.success && result.data) {
                setConfig(result.data as LLMConfig);
                setActiveTab('configure');
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            alert('Failed to load configuration. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/llm-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config),
            });

            const result = await response.json();

            if (result.success) {
                alert('Configuration saved successfully!');
                // Reload configs after saving
                await loadConfigurations();
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            alert('Failed to save configuration. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleStarterChange = (index: number, value: string) => {
        const newStarters = [...config.conversationStarters];
        newStarters[index] = value;
        setConfig({ ...config, conversationStarters: newStarters });
    };

    const handleRemoveStarter = (index: number) => {
        setConfig({
            ...config,
            conversationStarters: config.conversationStarters.filter((_: string, i: number) => i !== index)
        });
    };

    const handleAddStarter = () => {
        setConfig({
            ...config,
            conversationStarters: [...config.conversationStarters, '']
        });
    };

    const handleCapabilityChange = (capability: keyof typeof config.capabilities) => {
        setConfig({
            ...config,
            capabilities: {
                ...config.capabilities,
                [capability]: !config.capabilities[capability]
            }
        });
    };

    const handleCreateNewAction = () => {
        console.log("Create new action clicked");
        // Implementation for creating new action
        setConfig({
            ...config,
            actions: [...config.actions, `action-${config.actions.length + 1}`]
        });
    };

    const handleCreateNew = () => {
        setConfig({
            name: '',
            description: '',
            instructions: '',
            conversationStarters: [
                'How can I improve my website\'s SEO?',
                'What are the latest SEO trends?',
                'Can you analyze my website\'s SEO?',
                'How to do keyword research effectively?',
                ''
            ],
            capabilities: {
                webBrowsing: false,
                imageGeneration: false,
                codeInterpreter: false
            },
            actions: []
        });
        setActiveTab('configure');
    };

    return (
        <React.Fragment>
            <Head>
                <title>LLM Configuration | Ahoum Voice Agent</title>
                <meta name="description" content="Configure your LLM agent settings" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <main className="min-h-screen bg-blue-900 p-4 flex items-center justify-center">
                <div className="w-full max-w-3xl bg-gray-900 rounded-xl shadow-xl overflow-hidden">
                    {/* Navigation */}
                    <div className="absolute top-4 left-4 z-10">
                        <Link href="/">
                            <div className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                                Back to Home
                            </div>
                        </Link>
                    </div>

                    {/* Tabs */}
                    <div className="flex bg-gray-800 mt-12">
                        <button
                            className={cn(
                                "px-6 py-4 text-center flex-1",
                                activeTab === 'create' ? 'bg-gray-800 text-white' : 'bg-gray-900 text-gray-400'
                            )}
                            onClick={() => setActiveTab('create')}
                        >
                            Create
                        </button>
                        <button
                            className={cn(
                                "px-6 py-4 text-center flex-1",
                                activeTab === 'configure' ? 'bg-gray-800 text-white' : 'bg-gray-900 text-gray-400'
                            )}
                            onClick={() => setActiveTab('configure')}
                        >
                            Configure
                        </button>
                    </div>

                    {/* Content based on active tab */}
                    {activeTab === 'create' ? (
                        <div className="p-6 space-y-6">
                            <h2 className="text-white text-xl font-bold mb-4">Saved Configurations</h2>

                            {loading ? (
                                <div className="text-white">Loading...</div>
                            ) : (
                                <>
                                    {savedConfigs.length === 0 ? (
                                        <div className="text-gray-400">No saved configurations found.</div>
                                    ) : (
                                        <div className="space-y-2">
                                            {savedConfigs.map((savedConfig, index) => (
                                                <div
                                                    key={index}
                                                    className="bg-gray-800 rounded-md p-4 cursor-pointer hover:bg-gray-700 transition-colors"
                                                    onClick={() => loadConfiguration(savedConfig.name)}
                                                >
                                                    <div className="text-white font-medium">{savedConfig.name}</div>
                                                    {savedConfig.description && (
                                                        <div className="text-gray-400 text-sm mt-1">{savedConfig.description}</div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    <div className="mt-6">
                                        <button
                                            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                                            onClick={handleCreateNew}
                                        >
                                            Create New Configuration
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ) : (
                        <div className="p-6 space-y-6">
                            {/* Form */}
                            <div>
                                <label className="block text-white mb-2">Name</label>
                                <input
                                    type="text"
                                    className="w-full bg-gray-800 border border-gray-700 rounded-md p-3 text-white"
                                    value={config.name}
                                    onChange={(e) => setConfig({ ...config, name: e.target.value })}
                                    placeholder="SEO Advisor"
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="block text-white mb-2">Description</label>
                                <input
                                    type="text"
                                    className="w-full bg-gray-800 border border-gray-700 rounded-md p-3 text-white"
                                    value={config.description}
                                    onChange={(e) => setConfig({ ...config, description: e.target.value })}
                                    placeholder="Casual and friendly, providing easy-to-understand SEO advice based on Google SERP analysis"
                                />
                            </div>

                            {/* Instructions */}
                            <div>
                                <label className="block text-white mb-2">Instructions</label>
                                <textarea
                                    className="w-full bg-gray-800 border border-gray-700 rounded-md p-3 text-white h-32 resize-none"
                                    value={config.instructions}
                                    onChange={(e) => setConfig({ ...config, instructions: e.target.value })}
                                    placeholder="SEO Advisor adopts a casual and friendly communication style, making SEO advice approachable and easy to understand..."
                                />
                            </div>

                            {/* Conversation starters */}
                            <div>
                                <label className="block text-white mb-2">Conversation starters</label>
                                <div className="space-y-2">
                                    {config.conversationStarters.map((starter, index) => (
                                        <div key={index} className="flex items-center">
                                            <input
                                                type="text"
                                                className="flex-1 bg-gray-800 border border-gray-700 rounded-md p-3 text-white"
                                                value={starter}
                                                onChange={(e) => handleStarterChange(index, e.target.value)}
                                                placeholder="Add a conversation starter"
                                            />
                                            <button
                                                className="ml-2 text-gray-400 hover:text-gray-200"
                                                onClick={() => handleRemoveStarter(index)}
                                            >
                                                <X size={20} />
                                            </button>
                                        </div>
                                    ))}
                                    <button
                                        className="text-blue-400 hover:text-blue-300 py-2"
                                        onClick={handleAddStarter}
                                    >
                                        + Add another starter
                                    </button>
                                </div>
                            </div>

                            {/* Knowledge */}
                            <div>
                                <label className="block text-white mb-2">Knowledge</label>
                                <button className="bg-gray-800 border border-gray-700 rounded-md px-4 py-2 text-white">
                                    Upload files
                                </button>
                            </div>

                            {/* Capabilities */}
                            <div>
                                <label className="block text-white mb-2">Capabilities</label>
                                <div className="space-y-2">
                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            id="webBrowsing"
                                            checked={config.capabilities.webBrowsing}
                                            onChange={() => handleCapabilityChange('webBrowsing')}
                                            className="mr-2"
                                        />
                                        <label htmlFor="webBrowsing" className="text-white">Web Browsing</label>
                                    </div>
                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            id="imageGeneration"
                                            checked={config.capabilities.imageGeneration}
                                            onChange={() => handleCapabilityChange('imageGeneration')}
                                            className="mr-2"
                                        />
                                        <label htmlFor="imageGeneration" className="text-white">DALL-E Image Generation</label>
                                    </div>
                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            id="codeInterpreter"
                                            checked={config.capabilities.codeInterpreter}
                                            onChange={() => handleCapabilityChange('codeInterpreter')}
                                            className="mr-2"
                                        />
                                        <label htmlFor="codeInterpreter" className="text-white">Code Interpreter</label>
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div>
                                <label className="block text-white mb-2">Actions</label>
                                <div className="mb-3">
                                    {config.actions.map((action, index) => (
                                        <div key={index} className="bg-gray-800 border border-gray-700 rounded-md p-3 mb-2 text-white">
                                            {action}
                                        </div>
                                    ))}
                                </div>
                                <button
                                    className="bg-gray-800 border border-gray-700 rounded-md px-4 py-2 text-white"
                                    onClick={handleCreateNewAction}
                                >
                                    Create new action
                                </button>
                            </div>

                            {/* Save Button */}
                            <div className="flex justify-end">
                                <button
                                    className={`bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-md ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    onClick={handleSave}
                                    disabled={loading}
                                >
                                    {loading ? 'Saving...' : 'Save Configuration'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </React.Fragment>
    );
} 